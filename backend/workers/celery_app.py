try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None

from backend.config import settings

if CELERY_AVAILABLE:
    celery_app = Celery(
        "automl",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=["backend.workers.tasks"],
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        worker_concurrency=4,
        task_soft_time_limit=1800,
        task_time_limit=2100,
        task_routes={
            "backend.workers.tasks.run_pipeline": {"queue": "training"},
        },
    )

    # Auto-discover tasks
    celery_app.autodiscover_tasks(["backend.workers"])
else:
    celery_app = None