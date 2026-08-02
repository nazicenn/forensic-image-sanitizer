from fastapi import APIRouter, File, UploadFile, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
import logging

from app.api.middleware.auth import validate_api_key
from app.api.middleware.rate_limit import limiter
from app.api.middleware.validator import validate_file_upload, calculate_file_hash
from app.core.exceptions import ValidationError
from app.db.session import AsyncSessionLocal
from app.db.crud import create_job

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Upload"], prefix="/upload")


@router.post("/")
@limiter.limit("10/minute")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    clean_level: str = "medium",
    api_key: str = Depends(validate_api_key),
):
    """
    Upload an image for forensic sanitization.
    """
    try:
        # Validate file
        validated_file = await validate_file_upload(file)

        # Calculate file hash
        file_hash = calculate_file_hash(validated_file)

        # Get file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # Generate job ID
        job_id = uuid.uuid4()

        # Create job in database
        async with AsyncSessionLocal() as db:
            job = await create_job(
                db,
                original_filename=file.filename,
                clean_level=clean_level,
                job_metadata={
                    'file_hash': file_hash,
                    'content_type': file.content_type,
                    'size': file_size,
                }
            )

        return JSONResponse(
            status_code=202,
            content={
                "job_id": str(job.id),
                "original_filename": file.filename,
                "clean_level": clean_level,
                "status": "pending",
                "message": "Image uploaded successfully. Processing queued.",
                "status_url": f"/api/v1/status/{job.id}",
            }
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))