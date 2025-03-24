from django.dispatch import receiver

from django_resilient_webhook.signals import drw_event_parse_success, drw_event_receive, drw_event_reject


@receiver(drw_event_receive)
def receive_handler(request, **kwargs):
    print("drw_event_receive", request, request.body)


@receiver(drw_event_parse_success)
def success_handler(payload, sender_endpoint, sender_webhook, dispatched, headers, request, **kwargs):
    print(
        "drw_event_parse_success", payload, sender_endpoint, sender_webhook, dispatched, headers, request, request.body
    )


@receiver(drw_event_reject)
def parse_fail_handler(request, **kwargs):
    print("drw_event_reject", request, request.body)
