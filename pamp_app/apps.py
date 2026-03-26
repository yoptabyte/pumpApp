from django.apps import AppConfig


class PampAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pamp_app'

    def ready(self) -> None:
        from . import signals  # noqa: F401
