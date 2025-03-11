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


class ReceivedEvent(Model):

    DISCARDED_DUPLICATE_TASK_NAME = "discard-duplicate-task-name"
    DISCARDED_OUT_OF_ORDER = "discard-out-of-order"
    REJECTED_OUT_OF_ORDER = "reject-out-of-order"
    ACCEPTED = "accepted"

    STATUS_CHOICES = [
        (DISCARDED_DUPLICATE_TASK_NAME, "Discarded duplicate task"),
        (REJECTED_OUT_OF_ORDER, "Rejected out of order"),
        (ACCEPTED, "Accepted"),
    ]

    id = UUIDField(primary_key=True, default=uuid4, help_text="Universally Unique ID")
    created = DateTimeField(blank=False, null=False, auto_now_add=True, help_text="Datetime the event was created")

    payload = JSONField(null=False, blank=False, default=dict, help_text="If provided, data posted to the endpoint")
    sender_endpoint = JSONField(
        null=False,
        blank=False,
        default=dict,
        help_text="The sender endpoint data which contains information about the sender Endpoint instance which posted this",
    )
    sender_webhook = JSONField(
        null=False,
        blank=False,
        default=dict,
        help_text="The sender webhook data which contains information about the sender Webhook instance which posted this",
    )
    dispatched_utc = DateTimeField(blank=False, null=False, help_text="UTC datetime the Endpoint was dispatched")
    headers = JSONField(null=False, blank=False, default=dict, help_text="The header data of the posted request")

    status = CharField(max_length=64, choices=STATUS_CHOICES, null=False, blank=False)
