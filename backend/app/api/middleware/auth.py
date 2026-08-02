"""
Authentication Middleware - API Key validation.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
import logging
from datetime import datetime
import traceback

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.crud import get_api_key, update_api_key_last_used
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Validate API key from request header.
    """
    if not api_key:
        logger.warning("API key missing from request")
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key header."
        )

    try:
        async with AsyncSessionLocal() as db:
            try:
                key_record = await get_api_key(db, api_key)
                logger.info(f"API key found: {key_record.name}")
            except NotFoundError:
                logger.warning(f"Invalid API key: {api_key[:8]}...")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )
            except Exception as e:
                logger.error(f"Database error while fetching API key: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=500,
                    detail="Database error during authentication"
                )

            if not key_record.is_active:
                logger.warning(f"Inactive API key: {api_key[:8]}...")
                raise HTTPException(
                    status_code=401,
                    detail="API key is inactive"
                )

            if key_record.expires_at and key_record.expires_at < datetime.utcnow():
                logger.warning(f"Expired API key: {api_key[:8]}...")
                raise HTTPException(
                    status_code=401,
                    detail="API key has expired"
                )

            # Update last used timestamp
            try:
                await update_api_key_last_used(db, api_key)
            except Exception as e:
                logger.warning(f"Failed to update last used: {e}")

            logger.info(f"API key validated: {key_record.name} ({api_key[:8]}...)")
            return api_key

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in validate_api_key: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


async def optional_auth(api_key: Optional[str] = Depends(api_key_header)) -> Optional[str]:
    """
    Optional authentication (for public endpoints).
    """
    if not api_key:
        return None

    try:
        return await validate_api_key(api_key)
    except HTTPException:
        return None