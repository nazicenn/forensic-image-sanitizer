"""
Celery Application Configuration
"""

from celery import Celery
from celery.schedules import crontab
import os
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "forensic_sanitizer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    result_expires=3600,  # 1 hour
    broker_connection_retry_on_startup=True,
)

# Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    "cleanup-old-jobs": {
        "task": "app.workers.tasks.cleanup_old_jobs",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        "args": (7,),  # Delete jobs older than 7 days
    },
    "health-check": {
        "task": "app.workers.tasks.health_check",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}

# Load task modules
celery_app.autodiscover_tasks(["app.workers"])


if __name__ == "__main__":
    celery_app.start()