
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI, Request, Depends, BackgroundTasks, Header
from app.api.api import api_router
from app.security.api_key import verify_api_key  # (unused here; OK if used in routes)
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

    # Verify DB connectivity before proceeding
    logger.info("Testing database connection...")
    ok = await DatabaseConnection.test_connection()
    if not ok:
        logger.error("Database connection test failed. Aborting startup.")
        # Raising triggers clean startup failure under uvicorn/gunicorn
        raise RuntimeError("Database connection test failed")

    # Initialize pooled connections/engines
    await DatabaseConnection.initialize()
    logger.info("Database connection pool initialized")

    # Robust background listener
    stop_event = asyncio.Event()

    async def continuous_listen():
        listener = VisitorEventListener()
        backoff = 1
        while not stop_event.is_set():
            try:
                await listener.listen_for_events()
                backoff = 1  # reset backoff after a successful iteration
            except asyncio.CancelledError:
                # Task is being cancelled during shutdown
                break
            except Exception as e:
                logger.exception("VisitorEventListener crashed; will retry with backoff")
                # modest capped backoff to avoid tight crash loops
                await asyncio.sleep(min(backoff, 30))
                backoff = min(backoff * 2, 30)
                continue
            # Normal cadence between polls
            await asyncio.sleep(10)

    task = asyncio.create_task(continuous_listen())

    logger.info("Application startup complete")
    try:
        yield
    finally:
        # Signal and cancel background task
        stop_event.set()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Close pools safely
        for db_name, pool in DatabaseConnection._pools.items():
            if pool:
                try:
                    await pool.close()
                    logger.info(f"Database connection pool closed for {db_name}")
                except Exception:
                    logger.exception(f"Error closing pool for {db_name}")

        for db_name, engine in DatabaseConnection._engines.items():
            if engine:
                try:
                    await engine.dispose()
                    logger.info(f"SQLAlchemy engine disposed for {db_name}")
                except Exception:
                    logger.exception(f"Error disposing engine for {db_name}")

        logger.info("Application shutdown complete")

app = FastAPI(
    title="VecApp AI Service",
    description="AI service for analyzing and summarizing follow-up interactions with visitors",
    version="1.0.0",
    lifespan=lifespan,
)

setup_middleware(app)
app.include_router(api_router)

# Configure rate limit identity function
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
