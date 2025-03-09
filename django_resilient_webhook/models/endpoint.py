from uuid import uuid4

from django.db.models import DateTimeField, JSONField, Model, SlugField, TextField, UUIDField

from django_resilient_webhook.models.event import DispatchEvent
from django_resilient_webhook.utilities.create_task import create_http_task
from django_resilient_webhook.utilities.event_processing import serialize_event
from django_resilient_webhook.utilities.settings import parse_queue_setting


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
