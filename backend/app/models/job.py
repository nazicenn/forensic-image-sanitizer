from sqlalchemy import Column, String, DateTime, Integer 
from app.db.session import Base 
 
class ProcessingJob(Base): 
    __tablename__ = "processing_jobs" 
    id = Column(Integer, primary_key=True, index=True) 
    filename = Column(String(255)) 
    status = Column(String(50), default="pending") 
