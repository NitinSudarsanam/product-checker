"""
Startup script to fix Windows asyncio policy before running the app
"""
import sys
import asyncio

# Must be set before any async operations
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Now import and run the app
if __name__ == "__main__":
    from app.main import app
    import uvicorn
    from app.config import settings
    
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False  # Disable reload to prevent event loop issues
    )
