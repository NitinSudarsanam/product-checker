from __future__ import annotations

from celery import Celery
from app.config import settings


def make_celery() -> Celery:
    celery_app = Celery(
        "ubique_product_checker",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=["app.tasks.scan_tasks"],
    )

    celery_app.conf.update(
        task_track_started=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        broker_connection_retry_on_startup=True,
    )

    return celery_app


celery_app = make_celery()

