from django.contrib import admin

from django_resilient_webhook.models import DispatchEvent, Endpoint, Webhook


admin.site.register(Endpoint)
admin.site.register(Webhook)
admin.site.register(DispatchEvent)
