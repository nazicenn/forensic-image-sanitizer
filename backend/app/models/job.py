from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.session import Base


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String(255), nullable=False)
    processed_filename = Column(String(255))
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Integer, default=0)
    clean_level = Column(String(50), default="medium")
    job_metadata = Column(JSON, default={})  # 'metadata' yerine 'job_metadata'
    error_message = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<ProcessingJob {self.id} - {self.status}>"