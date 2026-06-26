from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
    label = "profiles"
    verbose_name = "Profiles"

    def ready(self) -> None:
        # Connect the post_save signal that auto-creates a Profile per User.
        from apps.profiles import signals  # noqa: F401
