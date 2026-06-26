"""Celery application factory. Imported in config/__init__.py so @shared_task works."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("finpulse")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # pragma: no cover - operational helper
    """Trivial task used to confirm the worker is wired up."""
    print(f"Celery request: {self.request!r}")
