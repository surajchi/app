"""Run the active news provider through the pipeline to seed sample articles.

    python manage.py seed_news
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from apps.news.tasks import ingest_news


class Command(BaseCommand):
    help = "Ingest sample news via the configured provider + pipeline."

    def handle(self, *args: Any, **options: Any) -> None:
        created = ingest_news()
        self.stdout.write(self.style.SUCCESS(f"Ingested {created} new article(s)."))
