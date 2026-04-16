"""Celery 앱 인스턴스"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from celery import Celery
from backend.core.config import settings

app = Celery(
    "tickdeck",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker.tasks.generate"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
)
