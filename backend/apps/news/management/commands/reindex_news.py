"""Rebuild the OpenSearch news index from the database.

    python manage.py reindex_news
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Recreate and repopulate the OpenSearch news index."

    def handle(self, *args: Any, **options: Any) -> None:
        from search.news_index import reindex_all

        count = reindex_all()
        self.stdout.write(self.style.SUCCESS(f"Reindexed {count} article(s) into OpenSearch."))
