from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from slowapi.errors import RateLimitExceeded
import logging

from app.api.v1.endpoints import health, upload
from app.api.middleware.auth import validate_api_key
from app.api.middleware.rate_limit import limiter, rate_limit_handler
from app.api.middleware.validator import validate_file_upload
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Image Forensics Sanitizer - Remove all AI traces from images",
)

# --- ÖNEMLİ: app.state.limiter'ı ata ---
app.state.limiter = limiter
# ----------------------------------------

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
    allowed_hosts=["*"]  # Production'da belirli hostlar eklenmeli
)

# Rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


# Health check endpoint (public)
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Include routers
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