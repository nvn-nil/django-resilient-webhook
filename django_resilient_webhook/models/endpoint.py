from uuid import uuid4

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import (
    CASCADE,
    PROTECT,
    CharField,
    DateTimeField,
    ForeignKey,
    Index,
    JSONField,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    SlugField,
    TextField,
    UUIDField,
)


class DispatchEvent(Model):
    endpoint = ForeignKey(
        "django_resilient_webhook.Endpoint",
        on_delete=PROTECT,
        help_text="The webhook endpoint which was dispactched",
        related_name="dispatch_events",
    )
    webhook_integration = ForeignKey(
        "django_resilient_webhook.Webhook",
        on_delete=PROTECT,
        help_text="The Webhook through which the endpoint was dispactched",
        related_name="dispatch_events",
    )


class Endpoint(Model):
    created = DateTimeField(blank=False, null=False, auto_now_add=True, help_text="Datetime the Endpoint was created")
    last_modified = DateTimeField(
        blank=False,
        null=False,
        auto_now=True,
        help_text="Datetime of the last modification of the Endpoint",
    )

    id = UUIDField(primary_key=True, default=uuid4, help_text="Universally Unique ID")
    url = TextField(null=False, blank=False, help_text="URL to an post-able endpoint")
    label = SlugField(null=False, blank=False, help_text="Identifier for this endpoint")
    data = JSONField(
        null=True, blank=True, default={}, help_text="If provided, this data will be passed in along with the payload"
    )

    def post(self, url, payload, headers=None):
        pass


class Webhook(Model):
    version = CharField(max_length=64, null=False, blank=False)
    endpoints = ManyToManyField("django_resilient_webhook.Endpoint", help_text="Select endpoints for this integration")

    content_type = ForeignKey(ContentType, on_delete=CASCADE)
    object_id = PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        unique_together = ("content_type", "object_id", "version")
        indexes = [
            Index(fields=["content_type", "object_id"]),
        ]


class WebhookableModel(Model):
    webhook_integrations = GenericRelation("django_resilient_webhook.Webhook")

    class Meta:
        abstract = True
