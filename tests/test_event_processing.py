import json
from datetime import datetime

import pytest
from django.test import RequestFactory

from django_resilient_webhook.models import Endpoint, Webhook
from django_resilient_webhook.utilities.event_processing import deserialize_event, serialize_event


factory = RequestFactory()


class MockedRequest:
    def __init__(self, data=None, headers=None):
        if isinstance(data, dict):
            self.body = json.dumps(data)
        elif isinstance(data, str):
            self.body = data
        else:
            with open("tests/data/receiver/data.json", "r") as fi:
                self.body = json.load(fi)

        if isinstance(headers, dict):
            self.headers = headers
        else:
            with open("tests/data/receiver/header.json", "r") as fi:
                self.headers = json.load(fi)


@pytest.mark.django_db
def test_serializing_data_without_webhook():
    data = {"send": "data"}
    endpoint = Endpoint.objects.create(url="http://asd.gef", label="label", data={"stored": "data"})

    send_data, send_headers = serialize_event(data, endpoint, webhook=None, headers=None)
    assert send_data["payload"] == data
    assert send_data["endpoint"] == {
        "id": str(endpoint.id),
        "created": endpoint.created.isoformat(),
        "last_modified": endpoint.last_modified.isoformat(),
        "url": endpoint.url,
        "label": endpoint.label,
        "data": endpoint.data,
    }
    assert send_data["webhook"] is None
    assert datetime.fromisoformat(send_data["dispatched"]["utc"])
    assert datetime.fromisoformat(send_data["dispatched"]["local"])
    assert send_headers is None


@pytest.mark.django_db
def test_serializing_data_with_webhook():
    data = {"send": "data"}
    endpoint = Endpoint.objects.create(url="http://asd.gef", label="label", data={"stored": "data"})
    webhook = Webhook.objects.create(version="1")
    webhook.endpoints.set([endpoint])

    send_data, send_headers = serialize_event(data, endpoint, webhook=webhook, headers={"test-header": "test-value"})
    assert send_data["payload"] == data
    assert send_data["endpoint"] == {
        "id": str(endpoint.id),
        "created": endpoint.created.isoformat(),
        "last_modified": endpoint.last_modified.isoformat(),
        "url": endpoint.url,
        "label": endpoint.label,
        "data": endpoint.data,
    }
    assert send_data["webhook"] == {"version": webhook.version}
    assert datetime.fromisoformat(send_data["dispatched"]["utc"])
    assert datetime.fromisoformat(send_data["dispatched"]["local"])
    assert send_headers == {"test-header": "test-value"}


@pytest.mark.django_db
def test_deserializing_data():
    data = {"send": "data"}
    endpoint = Endpoint.objects.create(url="http://asd.gef", label="label", data={"stored": "data"})
    webhook = Webhook.objects.create(version="1")
    webhook.endpoints.set([endpoint])

    send_data, _ = serialize_event(data, endpoint, webhook=webhook)

    request = MockedRequest(data=send_data)  # Uses test/data/header.json as request headers
    parsed_data = deserialize_event(request)

    assert parsed_data["payload"] == send_data["payload"]
    assert parsed_data["sender_endpoint"] == send_data["endpoint"]
    assert parsed_data["sender_webhook"] == send_data["webhook"]
    assert parsed_data["dispatched"] == send_data["dispatched"]
    assert parsed_data["headers"]["Content-Type"] == "application/json"
    assert parsed_data["headers"]["X-Cloudtasks-Taskname"] == "46492913462763127871"
