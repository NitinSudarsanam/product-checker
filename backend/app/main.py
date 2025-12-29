from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.api import urls, scan, logs
from app.utils.logger import logger
import uvicorn
import asyncio
import sys

# Fix for Windows asyncio subprocess issue with Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Create FastAPI app
app = FastAPI(
    title="Ubique Buy-Button Detection API",
    description="API for detecting Add to Cart and Buy Now buttons on e-commerce websites",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Ubique Buy-Button Detection API...")
    await connect_to_mongo()
    logger.info("API is ready to accept requests")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API...")
    await close_mongo_connection()
    logger.info("API shutdown complete")


# Include routers
app.include_router(urls.router)
app.include_router(scan.router)
app.include_router(logs.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Ubique Buy-Button Detection API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    # Must set event loop policy before uvicorn.run on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.backend_reload
    )
