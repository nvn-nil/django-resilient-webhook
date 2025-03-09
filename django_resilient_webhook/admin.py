from django.contrib import admin

from django_resilient_webhook.models import DispatchEvent, Endpoint, Webhook
from django_resilient_webhook.models._base import Player


admin.site.register(Endpoint)
admin.site.register(Webhook)
admin.site.register(DispatchEvent)
admin.site.register(Player)
