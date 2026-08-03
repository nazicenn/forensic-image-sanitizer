from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi.errors import RateLimitExceeded
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from app.api.v1.endpoints import health, upload
from app.api.middleware.auth import validate_api_key
from app.api.middleware.rate_limit import limiter, rate_limit_handler
from app.api.middleware.validator import validate_file_upload
from app.core.config import settings
from app.core.metrics import metrics_middleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup logging
# from app.core.logging import setup_logging, get_logger
# logger = setup_logging(env="development" if settings.DEBUG else "production")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Image Forensics Sanitizer - Remove all AI traces from images",
)

# --- Set app state ---
app.state.limiter = limiter

# --- Middleware ---
# Metrics middleware first
app.middleware("http")(metrics_middleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


# --- Root endpoint ---
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


# --- Health check ---
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# --- Metrics endpoint ---
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# --- Readiness probe ---
@app.get("/ready")
async def readiness():
    """Kubernetes readiness probe."""
    # Check database, redis, minio connections
    # For now, return healthy
    return {"status": "ready"}


# --- Include routers ---
app.include_router(health.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )