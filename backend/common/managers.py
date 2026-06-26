"""Soft-delete manager/queryset used by domain models via BaseModel."""

from __future__ import annotations

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):  # type: ignore[override]
        """Bulk soft-delete: stamp deleted_at instead of removing rows."""
        return super().update(deleted_at=timezone.now())

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()

    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """Default manager that hides soft-deleted rows."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)
