from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.session import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(String(20), default="100/minute")
    
    # Datetime alanlarını güncelle
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime, onupdate=func.now())