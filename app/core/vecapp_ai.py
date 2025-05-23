from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import router as api_router
from app.security.auth import verify_token
from app.config.settings import Settings
from app.security.tenant_context import TenantContextMiddleware
from app.core.database import Database
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# Load settings
settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="VecApp AI Service",
    description="AI service for analyzing and summarizing follow-up interactions with visitors",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Add tenant context middleware
app.add_middleware(TenantContextMiddleware)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests"""
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Starting VecApp AI Service")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    logger.info("Shutting down VecApp AI Service")