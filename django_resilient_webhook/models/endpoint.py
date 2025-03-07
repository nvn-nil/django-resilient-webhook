import hashlib
from uuid import uuid4

from django.conf import settings
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

from django_resilient_webhook.utilities.create_task import create_http_task
from django_resilient_webhook.utilities.event_processing import serialize_event


def parse_queue_setting():
    queue_path = settings.DRW_GCP_WEBHOOK_QUEUE_PATH

    queue_path = queue_path.replace("projects/", "") if queue_path.startswith("projects/") else queue_path

    print("queue_path", queue_path.split("/"))

    project_id, _, location, _, queue_id = queue_path.split("/")
    return {"project_id": project_id, "location": location, "queue_id": queue_id}


def short_sha(value, digits=8):
    """Calculate a short sha from an input string, with a certain degree of uniqueness"""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:digits]


class DispatchEvent(Model):
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
        null=True, blank=True, default=dict, help_text="If provided, this data will be passed in along with the payload"
    )

    def __str__(self):
        return f"{self.label}, {self.created}"

    def post(self, payload, headers=None, webhook=None):
        queue_options = parse_queue_setting()

        data, headers = serialize_event(payload, self, webhook=webhook, headers=headers)

        task = create_http_task(
            project=queue_options["project_id"],
            location=queue_options["location"],
            queue=queue_options["queue_id"],
            url=self.url,
            json_payload=data,
            headers=headers,
        )

        DispatchEvent.objects.create(
            dispatched=data["dispatched"]["utc"], endpoint=self, webhook=webhook, payload=data, task_name=task.name
        )


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

    def __str__(self):
        return f"{self.content_type} {self.object_id}, v{self.version}"

    def post(self, endpoint_label, payload, headers=None):
        endpoints = self.endpoints.filter(label=endpoint_label)

        for endpoint in endpoints:
            endpoint.post(payload, headers=headers, webhook=self)


class WebhookableModel(Model):
    webhook_integrations = GenericRelation("django_resilient_webhook.Webhook")

    class Meta:
        abstract = True
