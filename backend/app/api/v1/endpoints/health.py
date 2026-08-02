from fastapi import APIRouter, Depends
from app.api.middleware.auth import optional_auth

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(api_key: str = Depends(optional_auth)):
    """Health check endpoint (public)."""
    return {
        "status": "healthy",
        "service": "Forensic Image Sanitizer",
        "version": "0.1.0",
        "authenticated": api_key is not None
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    # Check database, Redis, MinIO etc.
    return {"status": "ready"}