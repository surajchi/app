"""Auto-create a Profile whenever a User is created."""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.profiles.models import Profile
from apps.users.models import User


@receiver(post_save, sender=User, dispatch_uid="profiles.ensure_profile")
def ensure_profile(sender, instance: User, created: bool, **kwargs: object) -> None:
    if created:
        Profile.objects.get_or_create(user=instance)
