from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Model, TextField

from django_resilient_webhook.signals import connect_signals_to_class


ALLOWED_WEBHOOK_EVENTS = ["create", "update", "delete"]


class WebhookableModel(Model):
    WEBHOOK_EVENTS = []

    webhooks = GenericRelation("django_resilient_webhook.Webhook")

    def __init_subclass__(cls, **kwargs):
        connect_signals_to_class(cls)
        super().__init_subclass__(**kwargs)

    def save(self, *args, **kwargs):
        errored = [event for event in self.WEBHOOK_EVENTS if event not in ALLOWED_WEBHOOK_EVENTS]
        if errored:
            raise TypeError(f"Event{'s' if len(errored) > 1 else ''} not allowed as WEBHOOK_EVENTS. {errored}")

        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class Player(WebhookableModel):
    WEBHOOK_EVENTS = ["create"]

    name = TextField()
