from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DRWAppConfig(AppConfig):
    """Configuration for the django_resilient_webhook application"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_resilient_webhook"
    verbose_name = _("Django Resilient Webhook")

    def ready(self):
        from . import signals  # noqa:F401, pylint: disable=unused-import, import-outside-toplevel
