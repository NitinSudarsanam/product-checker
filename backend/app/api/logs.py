from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.schemas import LogEntry, StatsResponse
from app.database import get_database
from app.utils.logger import logger
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("", response_model=List[LogEntry])
async def get_logs(
    event_type: str = None,
    level: str = None,
    hours: int = 24,
    limit: int = 100,
    skip: int = 0
):
    """Get system logs with filtering"""
    try:
        db = get_database()
        
        # Build query
        query = {}
        
        # Filter by time
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        query["timestamp"] = {"$gte": time_threshold}
        
        if event_type:
            query["event_type"] = event_type
        if level:
            query["level"] = level.upper()
        
        # Fetch logs
        cursor = db.logs.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for log in logs:
            log["id"] = str(log["_id"])
            del log["_id"]
        
        return logs
    
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch logs: {str(e)}"
        )


@router.delete("", status_code=status.HTTP_200_OK)
async def clear_logs(older_than_days: int = 30):
    """Clear logs older than specified days"""
    try:
        db = get_database()
        
        # Calculate threshold
        threshold = datetime.utcnow() - timedelta(days=older_than_days)
        
        result = await db.logs.delete_many({"timestamp": {"$lt": threshold}})
        
        logger.info(f"Cleared {result.deleted_count} old logs")
        
        return {
            "message": f"Cleared logs older than {older_than_days} days",
            "deleted_count": result.deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear logs: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""
    try:
        db = get_database()
        
        # Count URLs
        total_urls = await db.urls.count_documents({})
        
        # Count total scans
        total_scans = await db.scan_results.count_documents({})
        
        # Count by status
        available_count = await db.scan_results.count_documents({"status": "available"})
        unavailable_count = await db.scan_results.count_documents({"status": "unavailable"})
        error_count = await db.scan_results.count_documents({"status": "error"})
        
        return {
            "total_urls": total_urls,
            "total_scans": total_scans,
            "available_count": available_count,
            "unavailable_count": unavailable_count,
            "error_count": error_count
        }
    
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )
