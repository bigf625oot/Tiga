import os
from celery import Celery
from app.core.config import settings

# Construct Redis URL from existing settings
redis_host = settings.REDIS_HOST
redis_port = settings.REDIS_PORT
redis_db = getattr(settings, "CELERY_REDIS_DB", 1) # Use a different DB for celery by default
redis_password = settings.REDIS_PASSWORD

if redis_password:
    broker_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
else:
    broker_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

# Initialize Celery app
celery_app = Celery(
    "tiga_task_engine",
    broker=broker_url,
    backend=broker_url,
    include=["app.services.platform.task_engine.adapters.celery_worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit by default
)
