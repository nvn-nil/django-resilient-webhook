import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from django_resilient_webhook.signals import drw_event_parse_fail, drw_event_parse_success, drw_event_receive
from django_resilient_webhook.utilities.event_processing import deserialize_event


logger = logging.getLogger(__name__)


@csrf_exempt
def webhook_handler(request):
    if request.method == "POST":
        drw_event_receive.send(sender=None, request=request)

        data = deserialize_event(request)

        drw_event_parse_success.send(
            sender=None,
            payload=data["payload"],
            sender_endpoint=data["sender_endpoint"],
            sender_webhook=data["sender_webhook"],
            dispatched=data["dispatched"],
            headers=data["headers"],
            request=request,
        )

        return HttpResponse(status=201)
    else:
        drw_event_parse_fail.send(sender=None, request=request)
        return HttpResponse(status=405)
