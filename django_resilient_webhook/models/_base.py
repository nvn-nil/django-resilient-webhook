from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Model


class WebhookableModel(Model):
    webhook_integrations = GenericRelation("django_resilient_webhook.Webhook")

    class Meta:
        abstract = True
