from django.urls import re_path

from django_resilient_webhook.views import webhook_handler


app_name = "django_resilient_webhook"

urlpatterns = [
    re_path(r"^receiver/$", webhook_handler, name="drw-webhook-handler"),
]
