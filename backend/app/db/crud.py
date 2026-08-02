from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime
from typing import Optional, List

from app.models.job import ProcessingJob, JobStatus
from app.models.api_key import APIKey
from app.core.exceptions import NotFoundError, ValidationError


# ============ JOB CRUD ============

async def create_job(
    db: AsyncSession,
    original_filename: str,
    clean_level: str = "medium",
    job_metadata: dict = None,
) -> ProcessingJob:
    """Create a new processing job."""
    job = ProcessingJob(
        original_filename=original_filename,
        clean_level=clean_level,
        job_metadata=job_metadata or {},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: UUID) -> ProcessingJob:
    """Get a job by ID."""
    result = await db.execute(
        select(ProcessingJob).where(ProcessingJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError(f"Job with ID {job_id} not found")
    return job


async def get_jobs(
    db: AsyncSession,
    status: Optional[JobStatus] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[ProcessingJob]:
    """Get jobs with optional status filter."""
    query = select(ProcessingJob)
    if status:
        query = query.where(ProcessingJob.status == status)
    query = query.order_by(ProcessingJob.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


async def update_job_status(
    db: AsyncSession,
    job_id: UUID,
    status: JobStatus,
    error_message: str = None,
    progress: int = None,
) -> ProcessingJob:
    """Update job status."""
    job = await get_job(db, job_id)
    job.status = status
    job.updated_at = datetime.utcnow()

    if error_message:
        job.error_message = error_message

    if progress is not None:
        job.progress = progress

    if status == JobStatus.COMPLETED:
        job.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(job)
    return job


async def update_job_processed_filename(
    db: AsyncSession,
    job_id: UUID,
    processed_filename: str,
) -> ProcessingJob:
    """Update processed filename."""
    job = await get_job(db, job_id)
    job.processed_filename = processed_filename
    job.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(job)
    return job


# ============ API KEY CRUD ============

async def create_api_key(
    db: AsyncSession,
    name: str,
    rate_limit: str = "100/minute",
) -> APIKey:
    """Create a new API key."""
    import secrets
    key = secrets.token_urlsafe(32)

    api_key = APIKey(
        key=key,
        name=name,
        rate_limit=rate_limit,
    )
    db.add(api_key)
    try:
        await db.commit()
        await db.refresh(api_key)
    except IntegrityError:
        await db.rollback()
        raise ValidationError("API key already exists")
    return api_key


async def get_api_key(db: AsyncSession, key: str) -> APIKey:
    """Get API key by key string."""
    result = await db.execute(
        select(APIKey).where(APIKey.key == key, APIKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise NotFoundError("Invalid or inactive API key")
    return api_key


async def update_api_key_last_used(
    db: AsyncSession,
    key: str,
) -> None:
    """Update API key last used timestamp."""
    result = await db.execute(
        update(APIKey)
        .where(APIKey.key == key)
        .values(last_used_at=datetime.utcnow())
    )
    await db.commit()


async def revoke_api_key(
    db: AsyncSession,
    key: str,
) -> None:
    """Revoke an API key."""
    result = await db.execute(
        update(APIKey)
        .where(APIKey.key == key)
        .values(is_active=False)
    )
    await db.commit()