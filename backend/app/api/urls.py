from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.schemas import URLCreateRequest, URLModel, URLResponse
from app.database import get_database
from app.utils.logger import logger, log_to_database
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/urls", tags=["URLs"])


@router.post("/add", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_urls(request: URLCreateRequest):
    """Add single or multiple URLs to the database"""
    try:
        db = get_database()
        
        # Prepare URL documents
        url_docs = []
        for url in request.urls:
            # Check if URL already exists
            existing = await db.urls.find_one({"url": url})
            if not existing:
                url_docs.append({
                    "url": url,
                    "created_at": datetime.utcnow(),
                    "group_name": request.group_name
                })
        
        if not url_docs:
            return {
                "message": "All URLs already exist",
                "added_count": 0,
                "duplicate_count": len(request.urls)
            }
        
        # Insert URLs
        result = await db.urls.insert_many(url_docs)
        
        # Log to database
        await log_to_database(
            db,
            "urls_added",
            {
                "count": len(result.inserted_ids),
                "group": request.group_name
            }
        )
        
        logger.info(f"Added {len(result.inserted_ids)} URLs")
        
        return {
            "message": f"Successfully added {len(result.inserted_ids)} URLs",
            "added_count": len(result.inserted_ids),
            "duplicate_count": len(request.urls) - len(url_docs)
        }
    
    except Exception as e:
        logger.error(f"Error adding URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add URLs: {str(e)}"
        )


@router.get("", response_model=List[URLResponse])
async def get_urls(group_name: str = None, limit: int = 100, skip: int = 0):
    """Get all stored URLs with optional filtering"""
    try:
        db = get_database()
        
        # Build query
        query = {}
        if group_name:
            query["group_name"] = group_name
        
        # Fetch URLs
        cursor = db.urls.find(query).sort("created_at", -1).skip(skip).limit(limit)
        urls = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for url in urls:
            url["id"] = str(url["_id"])
            del url["_id"]
        
        return urls
    
    except Exception as e:
        logger.error(f"Error fetching URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch URLs: {str(e)}"
        )


@router.get("/{url_id}", response_model=URLResponse)
async def get_url(url_id: str):
    """Get a specific URL by ID"""
    try:
        db = get_database()
        
        if not ObjectId.is_valid(url_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL ID format"
            )
        
        url = await db.urls.find_one({"_id": ObjectId(url_id)})
        
        if not url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )
        
        url["id"] = str(url["_id"])
        del url["_id"]
        
        return url
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch URL: {str(e)}"
        )


@router.delete("/{url_id}", status_code=status.HTTP_200_OK)
async def delete_url(url_id: str):
    """Delete a URL by ID"""
    try:
        db = get_database()
        
        if not ObjectId.is_valid(url_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL ID format"
            )
        
        result = await db.urls.delete_one({"_id": ObjectId(url_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )
        
        # Also delete associated scan results
        await db.scan_results.delete_many({"url_id": url_id})
        
        # Log to database
        await log_to_database(
            db,
            "url_deleted",
            {"url_id": url_id}
        )
        
        logger.info(f"Deleted URL with ID: {url_id}")
        
        return {"message": "URL deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete URL: {str(e)}"
        )


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_all_urls():
    """Delete all URLs and their scan results"""
    try:
        db = get_database()
        
        url_result = await db.urls.delete_many({})
        scan_result = await db.scan_results.delete_many({})
        
        # Log to database
        await log_to_database(
            db,
            "all_urls_deleted",
            {
                "urls_deleted": url_result.deleted_count,
                "scans_deleted": scan_result.deleted_count
            }
        )
        
        logger.info(f"Deleted all URLs ({url_result.deleted_count}) and scans ({scan_result.deleted_count})")
        
        return {
            "message": "All URLs and scan results deleted successfully",
            "urls_deleted": url_result.deleted_count,
            "scans_deleted": scan_result.deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error deleting all URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all URLs: {str(e)}"
        )
