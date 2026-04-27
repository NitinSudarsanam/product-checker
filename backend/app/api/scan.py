import asyncio
import time
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from app.models.schemas import ScanRequest, ScanResult, ScanJobStatus
from app.database import get_database
from app.utils.logger import logger, log_to_database
from app.config import settings
from bson import ObjectId
import uuid

from scraper import scrape_url

router = APIRouter(prefix="/api/scan", tags=["Scan"])

@router.post("/run", response_model=dict)
async def run_scan(request: ScanRequest):
    """Trigger a scan by creating a job and enqueueing work to the worker queue."""
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

        urls_to_scan = await db.urls.find(query).to_list(length=None)
        if not urls_to_scan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No URLs found to scan. Add URLs first."
            )

        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        job_doc = {
            "job_id": job_id,
            "status": "queued",
            "created_at": now,
            "started_at": None,
            "finished_at": None,
            "total_urls": len(urls_to_scan),
            "completed": 0,
            "success": 0,
            "error": 0,
            "rate_urls_per_sec": None,
            "eta_seconds": None,
            "last_update_at": now,
            "url_ids": request.url_ids,
            "method_counts": {"scrapingbee": 0, "playwright": 0, "static": 0},
        }
        await db.scan_jobs.insert_one(job_doc)

        # Enqueue worker fan-out
        from app.celery_app import celery_app
        celery_app.send_task("app.tasks.scan_tasks.enqueue_scan", args=[job_id, request.url_ids])

        logger.info(f"Scan job queued job_id={job_id} urls={len(urls_to_scan)}")
        return {
            "message": f"Scan queued for {len(urls_to_scan)} URLs",
            "job_id": job_id,
            "url_count": len(urls_to_scan),
            "status": "queued",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scan: {str(e)}"
        )


@router.get("/{job_id}/status", response_model=ScanJobStatus)
async def get_job_status(job_id: str):
    """Return progress for a specific scan job."""
    try:
        db = get_database()
        job = await db.scan_jobs.find_one({"job_id": job_id})
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        job["id"] = str(job["_id"])
        del job["_id"]

        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scan job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch job status: {str(e)}"
        )


@router.get("/status", response_model=dict)
async def get_scan_status():
    """Compatibility shim: true if any job is queued/running."""
    try:
        db = get_database()
        active = await db.scan_jobs.count_documents({"status": {"$in": ["queued", "running"]}})
        return {"scanning": active > 0}
    except Exception:
        return {"scanning": False}


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
