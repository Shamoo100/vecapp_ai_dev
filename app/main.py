from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from app.api.api import api_router
from app.security.api_key import verify_api_key
from app.database.repositories.connection import DatabaseConnection
from dotenv import load_dotenv
from app.config.settings import get_settings
from app.api.middleware import setup_middleware, limiter, get_identifier
import logging
import os
from app.tests.test_db_connection import test_database_connection
from fastapi import FastAPI, BackgroundTasks  
from app.events.visitor_event_listener import VisitorEventListener
import asyncio  # For loop
from app.database.repositories.tenant_context import TenantContextMiddleware, TenantContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# Force reload environment variables before any imports
load_dotenv(override=True)

# Load settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup logic
    logger.info("Environment variables loaded from .env file")
    
    # Test database connection on startup
    logger.info("Testing database connection...")
    if not await test_database_connection():
        logger.error("Database connection test failed. Exiting application.")
        import sys
        sys.exit(1)
    logger.info("Database connection test passed")

    async def continuous_listen():
            while True:
                await VisitorEventListener.listen_for_events()
                await asyncio.sleep(10)  # Poll every 10 seconds
        
    task = asyncio.create_task(continuous_listen())
    
    # Initialize database connection pool
    await DatabaseConnection.initialize()
    logger.info("Database connection pool initialized")
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown logic
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass  # Expected on shutdown
    # Close all database pools
    for db_name, pool in DatabaseConnection._pools.items():
        if pool:
            await pool.close()
            logger.info(f"Database connection pool closed for {db_name}")
    
    # Close all SQLAlchemy engines
    for db_name, engine in DatabaseConnection._engines.items():
        if engine:
            await engine.dispose()
            logger.info(f"SQLAlchemy engine disposed for {db_name}")
    
    logger.info("Application shutdown complete")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="VecApp AI Service",
    description="AI service for analyzing and summarizing follow-up interactions with visitors",
    version="1.0.0",
    lifespan=lifespan
)

# Set up all middleware
setup_middleware(app)

# Include API router
app.include_router(api_router)

# Update limiter to use custom identifier function
limiter.key_func = get_identifier

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests"""
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Apply global rate limit to all routes
# This is in addition to any route-specific limits
@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    """Root endpoint with rate limiting"""
    return {"message": "VecApp AI Service API"}

# Note: For route-specific rate limits, use the @limiter.limit decorator
# Example: @router.get("/endpoint") @limiter.limit("10/minute") async def endpoint(request: Request): ...
