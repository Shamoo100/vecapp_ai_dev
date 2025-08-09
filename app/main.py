from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from app.api.api import api_router
from app.security.api_key import verify_api_key
from app.database.repositories.connection import DatabaseConnection
from dotenv import load_dotenv
from app.config.settings import get_settings
from app.api.middleware import setup_middleware, limiter, get_identifier
import logging
import asyncio
from app.events.visitor_event_listener import VisitorEventListener

# Load environment variables early
load_dotenv(override=True)

# Load settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Environment variables loaded from .env file")
    
    logger.info("Testing database connection...")
    if not await DatabaseConnection.test_connection():
        logger.error("Database connection test failed. Exiting application.")
        import sys
        sys.exit(1)
    logger.info("Database connection test passed")

    async def continuous_listen():
        listener = VisitorEventListener()
        while True:
            await listener.listen_for_events()
            await asyncio.sleep(10)

    task = asyncio.create_task(continuous_listen())

    await DatabaseConnection.initialize()
    logger.info("Database connection pool initialized")
    logger.info("Application startup complete")

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    for db_name, pool in DatabaseConnection._pools.items():
        if pool:
            await pool.close()
            logger.info(f"Database connection pool closed for {db_name}")

    for db_name, engine in DatabaseConnection._engines.items():
        if engine:
            await engine.dispose()
            logger.info(f"SQLAlchemy engine disposed for {db_name}")

    logger.info("Application shutdown complete")

app = FastAPI(
    title="VecApp AI Service",
    description="AI service for analyzing and summarizing follow-up interactions with visitors",
    version="1.0.0",
    lifespan=lifespan
)

setup_middleware(app)
app.include_router(api_router)

limiter.key_func = get_identifier

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    return {"message": "VecApp AI Service API"}

"""Note: For route-specific rate limits, use the @limiter.limit decorator."""
