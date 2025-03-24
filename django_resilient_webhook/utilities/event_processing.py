import json
import logging
from datetime import datetime, timezone

from django.http import HttpResponse

from django_resilient_webhook.signals import (
    drw_event_discard,
    drw_event_parse_success,
    drw_event_receive,
    drw_event_reject,
)


logger = logging.getLogger(__name__)


def respond_to_event(status_code, request, event=None, status=None):
    from django_resilient_webhook.models import ReceivedEvent

    if 200 <= status_code < 300:
        if status_code == 202:
            drw_event_parse_success.send(
                sender=None,
                event=event,
                request=request,
            )
        else:
            drw_event_discard.send(
                sender=None,
                event=event,
                request=request,
            )
        ReceivedEvent.objects.create(
            payload=event["payload"],
            sender_endpoint=event["sender_endpoint"],
            sender_webhook=event["sender_webhook"],
            dispatched_utc=datetime.fromisoformat(event["dispatched"]["utc"]),
            headers=dict(event["headers"]),
            status=status,
        )
    else:
        drw_event_reject.send(sender=None, request=request, event=event, status=status)

    return HttpResponse(status=status_code)


def process_webhook_request(request):
    """
    Check and accept or reject received event
        - Reject non-POST requests
        - Discard duplicate events
        - Discard out of order update events
        - Reject out of order update events before create event
    """
    if request.method == "POST":
        try:
            from django_resilient_webhook.models import ReceivedEvent

            drw_event_receive.send(sender=None, request=request)

            data = deserialize_event(request)

            filter_kwargs = {"headers__X-Cloudtasks-Taskname": data["headers"]["X-Cloudtasks-Taskname"]}
            duplicate_events = ReceivedEvent.objects.filter(**filter_kwargs)

            if duplicate_events:
                return respond_to_event(208, request, event=data, status=ReceivedEvent.DISCARDED_DUPLICATE_TASK_NAME)

            # Model event
            if data["payload"] and "model" in data["payload"]:
                if data["sender_endpoint"]["label"] in ["update", "delete"]:
                    received_create_event = ReceivedEvent.objects.filter(
                        payload__model=data["payload"]["model"],
                        payload__pk=data["payload"]["pk"],
                        sender_endpoint__label="create",
                    )
                    if not received_create_event:
                        # Reject it assuming this event was received out of order and 'create' might reach after a while
                        return respond_to_event(405, request, event=data, status=ReceivedEvent.REJECTED_OUT_OF_ORDER)

                filter_kwargs = {
                    # The model instance which triggered the event
                    "payload__model": data["payload"]["model"],
                    "payload__pk": data["payload"]["pk"],
                    # The label is one of create, update or delete
                    "sender_endpoint__label": data["sender_endpoint"]["label"],
                    # Reject the event a later event of the same label was processed
                    # Eg, if update which was triggered first reaches after an update triggered second due to some reason
                    # In this case, there's no reason to process the older but newly received event
                    "dispatched_utc__gte": datetime.fromisoformat(data["dispatched"]["utc"]),
                }
                more_recent_events = ReceivedEvent.objects.filter(**filter_kwargs)

                if more_recent_events:
                    return respond_to_event(208, request, event=data, status=ReceivedEvent.DISCARDED_OUT_OF_ORDER)

            return respond_to_event(202, request, event=data, status=ReceivedEvent.ACCEPTED)
        except Exception as e:
            logger.error("DRW failed to parse request due to error: \n%s", e)
            return respond_to_event(400, request)
    else:
        return respond_to_event(405, request)


def serialize_event(data, endpoint, webhook=None, headers=None):
    """Prepare payload for dispatch"""
    webhook_data = {"version": webhook.version} if webhook else None

    datetime_now_utc = datetime.now(timezone.utc)
    datetime_now_local = datetime.now()

    return {
        "payload": data,
        "endpoint": {
            "id": str(endpoint.id),
            "created": endpoint.created.isoformat(),
            "last_modified": endpoint.last_modified.isoformat(),
            "url": endpoint.url,
            "label": endpoint.label,
            "data": endpoint.data,
        },
        "webhook": webhook_data,
        "dispatched": {
            "utc": datetime_now_utc.isoformat(),
            "local": datetime_now_local.isoformat(),
        },
    }, headers


def deserialize_event(request):
    """Retrive information from compliant webhook"""
    data = json.loads(request.body)
    headers = request.headers

    required_fields = ["payload", "endpoint", "webhook", "dispatched"]
    if any(map(lambda x: x not in data, required_fields)):
        raise Exception(f"Required property missing from request. Required {required_fields}")

    payload = data["payload"]

    sender_endpoint = data["endpoint"]
    assert "id" in sender_endpoint
    assert "created" in sender_endpoint
    assert "last_modified" in sender_endpoint
    assert "url" in sender_endpoint
    assert "label" in sender_endpoint
    assert "data" in sender_endpoint

    sender_webhook = data["webhook"]
    if sender_webhook:
        assert "version" in sender_webhook

    sender_dispatched = data["dispatched"]
    assert "utc" in sender_dispatched
    assert "local" in sender_dispatched

    assert "Content-Length" in headers
    assert headers["Content-Type"] == "application/json"
    assert "Host" in headers
    assert "User-Agent" in headers
    assert "X-Cloudtasks-Taskname" in headers
    assert "X-Cloudtasks-Queuename" in headers

    return {
        "payload": payload,
        "sender_endpoint": sender_endpoint,
        "sender_webhook": sender_webhook,
        "dispatched": sender_dispatched,
        "headers": headers,
    }
