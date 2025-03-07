import json
from datetime import datetime, timezone


def serialize_event(data, endpoint, webhook=None, headers=None):
    """Prepare payload for dispatch"""
    webhook_data = (
        {
            "version": webhook.version,
            "content_type": {
                "app_labeled_name": webhook.content_type.app_labeled_name,
                "name": webhook.content_type.name,
                "app_label": webhook.content_type.app_label,
                "model": webhook.content_type.model,
            },
            "object_id": webhook.content_object.id,
        }
        if webhook
        else None
    )

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
        assert "content_type" in sender_webhook
        assert "object_id" in sender_webhook

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
