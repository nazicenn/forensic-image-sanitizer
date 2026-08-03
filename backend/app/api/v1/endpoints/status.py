from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from app.db.session import AsyncSessionLocal
from app.db.crud import get_job
from app.api.middleware.auth import validate_api_key

router = APIRouter(tags=["Status"], prefix="/status")


@router.get("/{job_id}")
async def get_job_status(
    job_id: str,
    api_key: str = Depends(validate_api_key),
):
    """Get job status by ID."""
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    async with AsyncSessionLocal() as db:
        try:
            job = await get_job(db, job_uuid)
        except Exception:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "id": str(job.id),
            "status": job.status.value if hasattr(job.status, 'value') else job.status,
            "progress": job.progress,
            "original_filename": job.original_filename,
            "processed_filename": job.processed_filename,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }