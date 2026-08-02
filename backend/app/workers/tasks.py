"""
Celery Tasks for Image Processing
"""

import asyncio
import logging
import time
from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta

from celery import Task, shared_task
from celery.exceptions import SoftTimeLimitExceeded

from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.db.crud import (
    create_job, get_job, update_job_status,
    update_job_processed_filename, get_jobs
)
from app.models.job import JobStatus
from app.services.sanitizer import ImageSanitizer, CleanLevel
from app.storage.minio import MinIOClient

logger = logging.getLogger(__name__)


class ProcessingTask(Task):
    """Base task with retry and error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 5}
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = True


@celery_app.task(
    bind=True,
    base=ProcessingTask,
    name="process_image",
    max_retries=3,
    time_limit=30 * 60,
    soft_time_limit=25 * 60,
)
def process_image(self, job_id: str, clean_level: str = "medium"):
    """
    Process an image asynchronously.

    Args:
        job_id: Job UUID
        clean_level: Cleaning level (light, medium, aggressive, forensic)
    """
    logger.info(f"Processing job {job_id} with level {clean_level}")

    try:
        # Update status to processing
        asyncio.run(_update_status(job_id, JobStatus.PROCESSING, progress=10))

        # Get job details
        job = asyncio.run(_get_job_details(job_id))
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"error": "Job not found"}

        # Get image from storage
        minio_client = MinIOClient()
        image_data = minio_client.get_image(job.original_filename)

        if not image_data:
            asyncio.run(_update_status(job_id, JobStatus.FAILED, error="Image not found"))
            return {"error": "Image not found"}

        # Update progress
        asyncio.run(_update_status(job_id, JobStatus.PROCESSING, progress=30))

        # Sanitize image
        sanitizer = ImageSanitizer()
        clean_level_enum = CleanLevel(clean_level.lower())

        result = sanitizer.sanitize(image_data, clean_level_enum)

        if not result.success:
            asyncio.run(_update_status(
                job_id, JobStatus.FAILED,
                error=result.error or "Processing failed"
            ))
            return {"error": result.error}

        # Update progress
        asyncio.run(_update_status(job_id, JobStatus.PROCESSING, progress=80))

        # Save processed image
        processed_filename = f"processed_{job_id}_{job.original_filename}"
        minio_client.save_image(processed_filename, result.image)

        # Update job with processed filename
        asyncio.run(_update_processed_filename(job_id, processed_filename))

        # Update progress and status
        asyncio.run(_update_status(job_id, JobStatus.COMPLETED, progress=100))

        logger.info(f"Job {job_id} completed successfully")

        return {
            "job_id": job_id,
            "status": "completed",
            "processed_filename": processed_filename,
            "metrics": result.metrics,
            "steps": result.steps,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Job {job_id} exceeded soft time limit")
        asyncio.run(_update_status(job_id, JobStatus.FAILED, error="Processing timeout"))
        return {"error": "Processing timeout"}

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")

        # Retry if possible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5 ** (self.request.retries + 1))

        asyncio.run(_update_status(job_id, JobStatus.FAILED, error=str(e)))
        return {"error": str(e)}


@celery_app.task(name="cleanup_old_jobs")
def cleanup_old_jobs(days: int = 7):
    """
    Clean up old jobs and their associated images.
    """
    logger.info(f"Cleaning up jobs older than {days} days")

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get old jobs
    asyncio.run(_cleanup_old_jobs(cutoff_date))

    return {"cleaned": True, "days": days}


@celery_app.task(name="health_check")
def health_check():
    """
    Health check task.
    """
    logger.info("Health check performed")
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ============ ASYNC HELPER FUNCTIONS ============

async def _update_status(job_id: str, status: JobStatus, progress: int = None, error: str = None):
    """Update job status in database."""
    async with AsyncSessionLocal() as db:
        await update_job_status(
            db,
            UUID(job_id),
            status,
            error_message=error,
            progress=progress
        )


async def _get_job_details(job_id: str):
    """Get job details from database."""
    async with AsyncSessionLocal() as db:
        return await get_job(db, UUID(job_id))


async def _update_processed_filename(job_id: str, filename: str):
    """Update processed filename in database."""
    async with AsyncSessionLocal() as db:
        await update_job_processed_filename(db, UUID(job_id), filename)


async def _cleanup_old_jobs(cutoff_date: datetime):
    """Clean up old jobs."""
    async with AsyncSessionLocal() as db:
        # Get old jobs
        old_jobs = await get_jobs(db, status=JobStatus.COMPLETED)
        # Filter by date
        # ... implementation


# ============ SYNC WRAPPERS FOR CELERY ============

def sync_update_status(job_id: str, status: JobStatus, progress: int = None, error: str = None):
    """Sync wrapper for update_status."""
    return asyncio.run(_update_status(job_id, status, progress, error))