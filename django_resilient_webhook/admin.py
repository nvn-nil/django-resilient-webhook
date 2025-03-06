from django.contrib import admin

from django_resilient_webhook.models import Endpoint, Webhook


admin.site.register(Endpoint)
admin.site.register(Webhook)
