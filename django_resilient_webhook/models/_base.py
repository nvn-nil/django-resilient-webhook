from django.db.models import ManyToManyField, Model

from django_resilient_webhook.signals import connect_signals_to_class


ALLOWED_WEBHOOK_EVENTS = ["create", "update", "delete"]


class WebhookableModel(Model):
    WEBHOOK_EVENTS = []
    WEBHOOK_SERIALIZED_FIELDS = ["pk"]

    webhooks = ManyToManyField(
        "django_resilient_webhook.Webhook",
        blank=True,
        help_text="Webhooks related to this object",
    )

    def __init_subclass__(cls, **kwargs):
        connect_signals_to_class(cls)
        super().__init_subclass__(**kwargs)

    def save(self, *args, **kwargs):
        errored = [event for event in self.WEBHOOK_EVENTS if event.split(":")[0] not in ALLOWED_WEBHOOK_EVENTS]
        if errored:
            raise TypeError(f"Event{'s' if len(errored) > 1 else ''} not allowed as WEBHOOK_EVENTS. {errored}")

        super().save(*args, **kwargs)

    def post(self, webhook_version, endpoint_label, payload, headers=None):
        for webhook in self.webhooks.filter(version=webhook_version, active=True):
            webhook.post(endpoint_label, payload, headers=headers)

    class Meta:
        abstract = True
