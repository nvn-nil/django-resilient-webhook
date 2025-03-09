from django.db.models import CharField, ManyToManyField, Model


class Webhook(Model):
    version = CharField(max_length=64, null=False, blank=False)
    endpoints = ManyToManyField("django_resilient_webhook.Endpoint", help_text="Select endpoints for this integration")

    def post(self, endpoint_label, payload, headers=None):
        endpoints = self.endpoints.filter(label=endpoint_label)

        for endpoint in endpoints:
            endpoint.post(payload, headers=headers, webhook=self)
