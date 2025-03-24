from uuid import uuid4

from django.db.models import BooleanField, CharField, DateTimeField, ManyToManyField, Model, SlugField, UUIDField


class Webhook(Model):
    created = DateTimeField(blank=False, null=False, auto_now_add=True, help_text="Datetime the webhook was created")
    last_modified = DateTimeField(
        blank=False,
        null=False,
        auto_now=True,
        help_text="Datetime of the last modification of the webhook",
    )

    id = UUIDField(primary_key=True, default=uuid4, help_text="Universally Unique ID")

    active = BooleanField(default=True, blank=False, null=False)
    label = SlugField(
        null=False,
        blank=False,
        help_text="Identifier for this webhook",
    )
    version = CharField(max_length=64, null=False, blank=False)
    endpoints = ManyToManyField("django_resilient_webhook.Endpoint", help_text="Select endpoints for this integration")

    def post(self, endpoint_label, payload, headers=None):
        endpoints = self.endpoints.filter(label=endpoint_label, active=True)

        for endpoint in endpoints:
            endpoint.post(payload, headers=headers, webhook=self)
