from __future__ import annotations

import asyncio
from asyncio import TimeoutError as AsyncioTimeoutError
from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId
from pymongo import MongoClient

from celery.exceptions import SoftTimeLimitExceeded

from app.celery_app import celery_app
from app.config import settings
from app.utils.logger import logger

from scraper import scrape_url  # noqa: E402


_mongo: Optional[MongoClient] = None
_db = None


def _get_db_sync():
    """Celery tasks are sync; use PyMongo to avoid event-loop coupling issues."""
    global _mongo, _db
    if _db is not None:
        return _db
    _mongo = MongoClient(settings.mongodb_url, maxPoolSize=settings.mongodb_max_pool_size)
    _db = _mongo[settings.mongodb_database]
    return _db


def _set_job_running(db, job_id: str):
    now = datetime.utcnow()
    db.scan_jobs.update_one(
        {"job_id": job_id, "status": "queued"},
        {"$set": {"status": "running", "started_at": now, "last_update_at": now}},
    )


def _is_job_cancelled(db, job_id: str) -> bool:
    job = db.scan_jobs.find_one({"job_id": job_id}, {"status": 1})
    return not job or job.get("status") == "cancelled"


def _compute_progress_fields(job: Dict[str, Any]) -> Dict[str, Any]:
    started_at = job.get("started_at")
    completed = int(job.get("completed") or 0)
    total = int(job.get("total_urls") or 0)
    if not started_at or completed <= 0:
        return {"rate_urls_per_sec": None, "eta_seconds": None}

    elapsed_s = max(0.001, (datetime.utcnow() - started_at).total_seconds())
    rate = completed / elapsed_s
    remaining = max(0, total - completed)
    eta = int(remaining / rate) if rate > 0 else None
    return {"rate_urls_per_sec": round(rate, 3), "eta_seconds": eta}


def _compute_availability_summary(job: Dict[str, Any]) -> str:
    """
    Summarize availability over successfully scraped URLs only:
    - all_available: all successful are available
    - none_available: all successful are unavailable
    - some_unavailable: mix of available/unavailable among successes
    - unknown: no successful results yet (or all errors)
    """
    available = int(job.get("available_count") or 0)
    unavailable = int(job.get("unavailable_count") or 0)
    success_total = available + unavailable
    if success_total <= 0:
        return "unknown"
    if available == success_total:
        return "all_available"
    if unavailable == success_total:
        return "none_available"
    return "some_unavailable"

def _finalize_job_if_done(db, job_id: str):
    job = db.scan_jobs.find_one({"job_id": job_id})
    if not job:
        return
    if job.get("status") in {"done", "failed", "cancelled"}:
        return
    if int(job.get("completed") or 0) < int(job.get("total_urls") or 0):
        return

    now = datetime.utcnow()
    db.scan_jobs.update_one(
        {"job_id": job_id, "status": {"$in": ["queued", "running"]}},
        {"$set": {"status": "done", "finished_at": now, "last_update_at": now}},
    )


@celery_app.task(name="app.tasks.scan_tasks.enqueue_scan")
def enqueue_scan(job_id: str, url_ids: Optional[List[str]] = None):
    """Fan-out task: enqueue one scrape task per URL."""
    db = _get_db_sync()
    _set_job_running(db, job_id)

    query: Dict[str, Any] = {}
    if url_ids:
        valid_ids = [ObjectId(uid) for uid in url_ids if ObjectId.is_valid(uid)]
        query["_id"] = {"$in": valid_ids}

    urls_to_scan = list(db.urls.find(query))
    if not urls_to_scan:
        now = datetime.utcnow()
        db.scan_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "finished_at": now, "last_update_at": now}},
        )
        return

    db.scan_jobs.update_one(
        {"job_id": job_id},
        {"$set": {"total_urls": len(urls_to_scan), "last_update_at": datetime.utcnow()}},
    )

    for url_doc in urls_to_scan:
        scrape_one_url.delay(job_id, str(url_doc["_id"]), url_doc["url"])


@celery_app.task(
    name="app.tasks.scan_tasks.scrape_one_url",
    soft_time_limit=int(getattr(settings, "celery_scrape_task_soft_time_limit", 1080) or 1080),
    time_limit=int(getattr(settings, "celery_scrape_task_time_limit", 1200) or 1200),
)
def scrape_one_url(job_id: str, url_id: str, url: str):
    """Scrape one URL, persist result, update job progress."""
    db = _get_db_sync()
    if _is_job_cancelled(db, job_id):
        return

    wall = int(getattr(settings, "scraper_per_url_task_timeout_seconds", 0) or 0)
    if wall > 0:
        per_url_timeout = wall
    else:
        st = int(settings.scraper_timeout)
        # Must exceed megastore Playwright (5× nav + variant probes + ScrapingBee latency).
        per_url_timeout = max(st + 60, st * 12 + 180)

    try:
        scan_data = asyncio.run(
            asyncio.wait_for(
                scrape_url(url, use_playwright=settings.scraper_use_playwright),
                timeout=per_url_timeout,
            )
        )

        result_doc = {
            "url": url,
            "url_id": url_id,
            "scanned_at": scan_data["scanned_at"],
            "add_to_cart": scan_data["add_to_cart"],
            "buy_now": scan_data["buy_now"],
            "status": scan_data["status"],
            "error_message": scan_data.get("error_message"),
            "response_time": scan_data.get("response_time"),
            "scrape_method": scan_data.get("scrape_method"),
            "html_primary_source": scan_data.get("html_primary_source"),
            "unavailability_override": scan_data.get("unavailability_override", False),
            "variants": scan_data.get("variants", {}),
            "variants_checked": scan_data.get("variants_checked", False),
            "job_id": job_id,
        }
        db.scan_results.insert_one(result_doc)

        method = (scan_data.get("scrape_method") or "").lower()
        method_inc = {f"method_counts.{method}": 1} if method in {"scrapingbee", "playwright", "static"} else {}
        status = str(scan_data.get("status") or "").lower()
        avail_inc: Dict[str, int] = {}
        if status == "available":
            avail_inc["available_count"] = 1
        elif status == "unavailable":
            avail_inc["unavailable_count"] = 1

        db.scan_jobs.update_one(
            {"job_id": job_id},
            {"$inc": {"completed": 1, "success": 1, **avail_inc, **method_inc}, "$set": {"last_update_at": datetime.utcnow()}},
        )

    except (TimeoutError, AsyncioTimeoutError):
        error_doc = {
            "url": url,
            "url_id": url_id,
            "scanned_at": datetime.utcnow(),
            "add_to_cart": False,
            "buy_now": False,
            "status": "error",
            "error_message": f"Scan timed out after {per_url_timeout}s",
            "scrape_method": "error",
            "html_primary_source": None,
            "job_id": job_id,
        }
        db.scan_results.insert_one(error_doc)
        db.scan_jobs.update_one(
            {"job_id": job_id},
            {"$inc": {"completed": 1, "error": 1}, "$set": {"last_update_at": datetime.utcnow()}},
        )
    except SoftTimeLimitExceeded:
        error_doc = {
            "url": url,
            "url_id": url_id,
            "scanned_at": datetime.utcnow(),
            "add_to_cart": False,
            "buy_now": False,
            "status": "error",
            "error_message": "Worker hit Celery soft time limit — raise celery_scrape_task_soft_time_limit or reduce per-URL work",
            "scrape_method": "error",
            "html_primary_source": None,
            "job_id": job_id,
        }
        db.scan_results.insert_one(error_doc)
        db.scan_jobs.update_one(
            {"job_id": job_id},
            {"$inc": {"completed": 1, "error": 1}, "$set": {"last_update_at": datetime.utcnow()}},
        )
    except Exception as e:
        error_doc = {
            "url": url,
            "url_id": url_id,
            "scanned_at": datetime.utcnow(),
            "add_to_cart": False,
            "buy_now": False,
            "status": "error",
            "error_message": str(e),
            "scrape_method": "error",
            "html_primary_source": None,
            "job_id": job_id,
        }
        db.scan_results.insert_one(error_doc)
        db.scan_jobs.update_one(
            {"job_id": job_id},
            {"$inc": {"completed": 1, "error": 1}, "$set": {"last_update_at": datetime.utcnow()}},
        )

    job = db.scan_jobs.find_one({"job_id": job_id})
    if job:
        derived = _compute_progress_fields(job)
        derived["availability_summary"] = _compute_availability_summary(job)
        db.scan_jobs.update_one(
            {"job_id": job_id},
            {"$set": {**derived, "last_update_at": datetime.utcnow()}},
        )
    _finalize_job_if_done(db, job_id)

