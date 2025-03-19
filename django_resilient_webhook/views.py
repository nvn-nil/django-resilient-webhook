import logging

from django.views.decorators.csrf import csrf_exempt

from django_resilient_webhook.utilities.event_processing import process_webhook_request


logger = logging.getLogger(__name__)


@csrf_exempt
def webhook_handler(request):
    return process_webhook_request(request)
