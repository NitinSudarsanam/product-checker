import asyncio
import time
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from app.models.schemas import ScanRequest, ScanResponse, ScanResult
from app.database import get_database
from app.utils.logger import logger, log_to_database
from app.config import settings
from bson import ObjectId
import sys
from pathlib import Path

scraper_path = Path(__file__).parent.parent.parent.parent / "scraper"
sys.path.insert(0, str(scraper_path))

from scraper import scrape_url

router = APIRouter(prefix="/api/scan", tags=["Scan"])

_scan_running = False
_last_scan_started: float = 0.0
_SCAN_COOLDOWN_SECONDS = 10  # min seconds between scan starts (10.2)


async def run_scan_task(url_ids: Optional[List[str]] = None):
    """Background task to run the scan."""
    global _scan_running
    try:
        await _do_scan(url_ids)
    finally:
        _scan_running = False


async def _do_scan(url_ids: Optional[List[str]] = None):
    try:
        db = get_database()

        query = {}
        if url_ids:
            valid_ids = [ObjectId(uid) for uid in url_ids if ObjectId.is_valid(uid)]
            query["_id"] = {"$in": valid_ids}

        cursor = db.urls.find(query)
        urls_to_scan = await cursor.to_list(length=None)

        if not urls_to_scan:
            logger.warning("No URLs found to scan")
            return

        logger.info(f"Starting scan for {len(urls_to_scan)} URLs")
        per_url_timeout = settings.scraper_timeout + 15  # buffer beyond scraper's own timeout

        results = []
        for url_doc in urls_to_scan:
            url = url_doc["url"]
            try:
                logger.info(f"Scanning: {url}")

                # Per-URL timeout wrapper (5.1) — prevents hung tasks
                scan_data = await asyncio.wait_for(
                    scrape_url(url, use_playwright=settings.scraper_use_playwright),
                    timeout=per_url_timeout
                )

                result_doc = {
                    "url": url,
                    "url_id": str(url_doc["_id"]),
                    "scanned_at": scan_data["scanned_at"],
                    "add_to_cart": scan_data["add_to_cart"],
                    "buy_now": scan_data["buy_now"],
                    "status": scan_data["status"],
                    "error_message": scan_data.get("error_message"),
                    "response_time": scan_data.get("response_time"),
                    "scrape_method": scan_data.get("scrape_method"),
                    "unavailability_override": scan_data.get("unavailability_override", False),
                    "variants": scan_data.get("variants", {}),
                    "variants_checked": scan_data.get("variants_checked", False),
                }

                await db.scan_results.insert_one(result_doc)
                results.append(result_doc)
                logger.info(f"Scan complete for {url}: status={scan_data['status']}")

            except asyncio.TimeoutError:
                logger.error(f"Per-URL timeout ({per_url_timeout}s) exceeded for {url}")
                error_doc = {
                    "url": url,
                    "url_id": str(url_doc["_id"]),
                    "scanned_at": datetime.utcnow(),
                    "add_to_cart": False,
                    "buy_now": False,
                    "status": "error",
                    "error_message": f"Scan timed out after {per_url_timeout}s",
                }
                await db.scan_results.insert_one(error_doc)
                results.append(error_doc)

            except Exception as e:
                logger.error(f"Error scanning {url}: {e}")
                error_doc = {
                    "url": url,
                    "url_id": str(url_doc["_id"]),
                    "scanned_at": datetime.utcnow(),
                    "add_to_cart": False,
                    "buy_now": False,
                    "status": "error",
                    "error_message": str(e),
                }
                await db.scan_results.insert_one(error_doc)
                results.append(error_doc)

        await log_to_database(
            db,
            "scan_completed",
            {
                "total_urls": len(urls_to_scan),
                "successful": len([r for r in results if r["status"] != "error"]),
            }
        )
        logger.info(f"Scan completed for {len(results)} URLs")

    except Exception as e:
        logger.error(f"Error in scan task: {e}")


@router.post("/run", response_model=dict)
async def run_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Trigger a manual scan. Returns 409 if scan already in progress."""
    global _scan_running, _last_scan_started

    # Prevent double-scan (5.5)
    if _scan_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scan is already in progress. Wait for it to complete."
        )

    # Rate limit: prevent rapid repeated triggers (10.2)
    elapsed_since_last = time.time() - _last_scan_started
    if elapsed_since_last < _SCAN_COOLDOWN_SECONDS:
        wait = int(_SCAN_COOLDOWN_SECONDS - elapsed_since_last) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {wait}s before starting another scan."
        )

    try:
        db = get_database()

        if request.url_ids:
            for url_id in request.url_ids:
                if not ObjectId.is_valid(url_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid URL ID: {url_id}"
                    )

        query = {}
        if request.url_ids:
            valid_ids = [ObjectId(uid) for uid in request.url_ids]
            query["_id"] = {"$in": valid_ids}

        url_count = await db.urls.count_documents(query)

        # Return early if nothing to scan (5.8)
        if url_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No URLs found to scan. Add URLs first."
            )

        # Set flag BEFORE adding task — prevents race where first poll fires
        # before background task acquires the old lock and sets the flag (was issue 1)
        _scan_running = True
        _last_scan_started = time.time()
        background_tasks.add_task(run_scan_task, request.url_ids)
        logger.info(f"Scan initiated for {url_count} URLs")

        return {
            "message": f"Scan started for {url_count} URLs",
            "url_count": url_count,
            "status": "running"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scan: {str(e)}"
        )


@router.get("/status", response_model=dict)
async def get_scan_status():
    """Check if a scan is currently running."""
    return {"scanning": _scan_running}


@router.get("/results", response_model=List[ScanResult])
async def get_scan_results(
    url: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 200,
    skip: int = 0
):
    """Get scan results with optional filtering"""
    try:
        db = get_database()

        query = {}
        if url:
            query["url"] = url
        if status_filter:
            query["status"] = status_filter

        cursor = db.scan_results.find(query).sort("scanned_at", -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)

        for result in results:
            result["id"] = str(result["_id"])
            del result["_id"]

        return results

    except Exception as e:
        logger.error(f"Error fetching scan results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan results: {str(e)}"
        )


@router.get("/results/latest", response_model=List[ScanResult])
async def get_latest_results(limit: int = 500):
    """Get the most recent scan result per URL"""
    try:
        db = get_database()

        pipeline = [
            {"$sort": {"scanned_at": -1}},
            {"$group": {"_id": "$url", "latest_result": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$latest_result"}},
            {"$sort": {"scanned_at": -1}},
            {"$limit": limit},
        ]

        results = await db.scan_results.aggregate(pipeline).to_list(length=limit)

        for result in results:
            result["id"] = str(result["_id"])
            del result["_id"]

        return results

    except Exception as e:
        logger.error(f"Error fetching latest results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch latest results: {str(e)}"
        )


@router.delete("/results", status_code=status.HTTP_200_OK)
async def clear_scan_results():
    """Clear all scan results"""
    try:
        db = get_database()

        result = await db.scan_results.delete_many({})

        await log_to_database(
            db,
            "scan_results_cleared",
            {"deleted_count": result.deleted_count}
        )

        logger.info(f"Cleared {result.deleted_count} scan results")

        return {
            "message": "All scan results cleared",
            "deleted_count": result.deleted_count
        }

    except Exception as e:
        logger.error(f"Error clearing scan results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear scan results: {str(e)}"
        )
