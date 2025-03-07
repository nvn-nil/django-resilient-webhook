from django.dispatch import receiver

from django_resilient_webhook.signals import drw_event_parse_fail, drw_event_parse_success, drw_event_receive


@receiver(drw_event_receive)
def receive_handler(request, **kwargs):
    print("drw_event_receive", request, request.body)


@receiver(drw_event_parse_success)
def success_handler(payload, sender_endpoint, sender_webhook, dispatched, headers, request, **kwargs):
    print(
        "drw_event_parse_success", payload, sender_endpoint, sender_webhook, dispatched, headers, request, request.body
    )


@receiver(drw_event_parse_fail)
def parse_fail_handler(request, **kwargs):
    print("drw_event_parse_fail", request, request.body)
