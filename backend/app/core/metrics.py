"""
Prometheus Metrics - Application monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from fastapi import Request, Response
import time
from typing import Optional

# ============ JOB METRICS ============

# Job counters
jobs_total = Counter(
    'fis_jobs_total',
    'Total number of processing jobs',
    ['status', 'clean_level']
)

jobs_processing = Gauge(
    'fis_jobs_processing',
    'Number of jobs currently processing'
)

jobs_queued = Gauge(
    'fis_jobs_queued',
    'Number of jobs currently queued'
)

# Job duration histogram
job_duration = Histogram(
    'fis_job_duration_seconds',
    'Job processing duration in seconds',
    ['clean_level'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

# ============ API METRICS ============

# API request counters
api_requests_total = Counter(
    'fis_api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status_code']
)

# API request duration
api_request_duration = Histogram(
    'fis_api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Active requests gauge
api_active_requests = Gauge(
    'fis_api_active_requests',
    'Number of active API requests',
    ['endpoint']
)

# ============ STORAGE METRICS ============

storage_usage = Gauge(
    'fis_storage_usage_bytes',
    'Storage usage in bytes',
    ['storage_type']
)

storage_files_total = Gauge(
    'fis_storage_files_total',
    'Total number of files in storage',
    ['storage_type']
)

# ============ SYSTEM METRICS ============

system_info = Info(
    'fis_system_info',
    'System information'
)

# Set system info
system_info.info({
    'version': '0.1.0',
    'python_version': '3.12',
    'environment': 'production'
})

# ============ DEPENDENCY METRICS ============

db_connection_status = Gauge(
    'fis_db_connection_status',
    'Database connection status (1=connected, 0=disconnected)'
)

redis_connection_status = Gauge(
    'fis_redis_connection_status',
    'Redis connection status (1=connected, 0=disconnected)'
)

minio_connection_status = Gauge(
    'fis_minio_connection_status',
    'MinIO connection status (1=connected, 0=disconnected)'
)


# ============ MIDDLEWARE ============

async def metrics_middleware(request: Request, call_next):
    """
    ASGI middleware for collecting request metrics.
    """
    # Start timer
    start_time = time.time()

    # Increment active requests
    endpoint = request.url.path
    api_active_requests.labels(endpoint=endpoint).inc()

    try:
        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        status_code = response.status_code

        api_requests_total.labels(
            endpoint=endpoint,
            method=request.method,
            status_code=status_code
        ).inc()

        api_request_duration.labels(
            endpoint=endpoint,
            method=request.method
        ).observe(duration)

        return response

    finally:
        # Decrement active requests
        api_active_requests.labels(endpoint=endpoint).dec()


# ============ HELPER FUNCTIONS ============

def increment_job_counter(status: str, clean_level: str = "medium"):
    """Increment job counter."""
    jobs_total.labels(status=status, clean_level=clean_level).inc()


def observe_job_duration(duration: float, clean_level: str = "medium"):
    """Observe job duration."""
    job_duration.labels(clean_level=clean_level).observe(duration)


def update_job_gauges(processing: int, queued: int):
    """Update job gauges."""
    jobs_processing.set(processing)
    jobs_queued.set(queued)


def update_storage_metrics(storage_type: str, usage_bytes: int, file_count: int):
    """Update storage metrics."""
    storage_usage.labels(storage_type=storage_type).set(usage_bytes)
    storage_files_total.labels(storage_type=storage_type).set(file_count)


def update_dependency_status(db: bool = True, redis: bool = True, minio: bool = True):
    """Update dependency connection status."""
    db_connection_status.set(1 if db else 0)
    redis_connection_status.set(1 if redis else 0)
    minio_connection_status.set(1 if minio else 0)