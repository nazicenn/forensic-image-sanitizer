"""
Rate Limiting Middleware - Limit API requests per client.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT],
    storage_uri="memory://",
    strategy="fixed-window",
)

# Rate limit exceeded handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler."""
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    # _rate_limit_exceeded_handler zaten Response döndürüyor, await kullanma
    return _rate_limit_exceeded_handler(request, exc)


def get_rate_limit(limit: str = None) -> str:
    """
    Get rate limit string.

    Args:
        limit: Custom limit string (e.g., "100/minute")

    Returns:
        str: Rate limit string
    """
    return limit or settings.RATE_LIMIT