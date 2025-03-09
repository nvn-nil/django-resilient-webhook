from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import CASCADE, CharField, ForeignKey, Index, ManyToManyField, Model, PositiveIntegerField


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
