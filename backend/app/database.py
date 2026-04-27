from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    db = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB and ensure indexes exist"""
    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=settings.mongodb_max_pool_size,
        )
        db.db = db.client[settings.mongodb_database]

        await db.client.server_info()
        logger.info("Successfully connected to MongoDB")

        # Indexes for scan_results
        await db.db.scan_results.create_index([("url", 1)])
        await db.db.scan_results.create_index([("url_id", 1)])
        await db.db.scan_results.create_index([("scanned_at", -1)])

        # Indexes for scan_jobs (job tracking / progress)
        await db.db.scan_jobs.create_index([("job_id", 1)], unique=True, background=True)
        await db.db.scan_jobs.create_index([("created_at", -1)], background=True)
        await db.db.scan_jobs.create_index([("status", 1)], background=True)

        # TTL index on logs — auto-expire entries older than 30 days
        await db.db.logs.create_index(
            [("timestamp", 1)],
            expireAfterSeconds=2592000,
            background=True
        )

        # Index for URL dedup lookup
        await db.db.urls.create_index([("url", 1)], unique=True, background=True)

        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    try:
        if db.client:
            db.client.close()
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")


def get_database():
    """Get database instance"""
    return db.db
