from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from app.api.api import router as api_router
from app.security.api_key import verify_api_key
from app.database.connection import Database
from dotenv import load_dotenv
from app.config.settings import get_settings
from app.api.middleware import setup_middleware, limiter, get_identifier
import logging
import os
from app.tests.test_db_connection import run_test as test_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# Test database connection on startup
if not test_db_connection():
    logger.error("Database connection test failed. Exiting application.")
    import sys
    sys.exit(1)

# Force reload environment variables before any imports
load_dotenv(override=True)

# Load settings
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup logic
    logger.info("Environment variables loaded from .env file")
    
    db = Database(settings.DATABASE_URL)
    await db.initialize()
    logger.info("Database connection pool initialized")
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown logic
    if hasattr(Database, '_pool') and Database._pool:
        await Database._pool.close()
    logger.info("Database connection pool closed")
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
