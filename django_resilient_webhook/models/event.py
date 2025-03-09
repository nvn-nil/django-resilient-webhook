from uuid import uuid4

from django.db.models import PROTECT, CharField, DateTimeField, ForeignKey, JSONField, Model, UUIDField


class DispatchEvent(Model):
    id = UUIDField(primary_key=True, default=uuid4, help_text="Universally Unique ID")
    dispatched = DateTimeField(
        blank=False, null=False, auto_now_add=True, help_text="Datetime the Endpoint was dispatched"
    )

    endpoint = ForeignKey(
        "django_resilient_webhook.Endpoint",
        on_delete=PROTECT,
        help_text="The webhook endpoint which was dispactched",
        related_name="dispatch_events",
    )
    webhook = ForeignKey(
        "django_resilient_webhook.Webhook",
        on_delete=PROTECT,
        null=True,
        blank=True,
        help_text="The Webhook through which the endpoint was dispactched",
        related_name="dispatch_events",
    )

    payload = JSONField(null=True, blank=True, default=dict, help_text="If provided, data posted to the endpoint")

    task_name = CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return f"{self.webhook}, {self.endpoint}, {self.task_name.split('/')[-1]}"
