import datetime
import json
from typing import Dict, Optional

from django.conf import settings
from google.cloud import tasks_v2
from google.protobuf import duration_pb2, timestamp_pb2


def create_http_task(
    project: str,
    location: str,
    queue: str,
    url: str,
    json_payload: Dict,
    scheduled_seconds_from_now: Optional[int] = None,
    task_id: Optional[str] = None,
    deadline_in_seconds: Optional[int] = None,
    headers: Optional[dict] = None,
) -> tasks_v2.Task:
    """Create an HTTP POST task with a JSON payload.

    :param str project: The project ID where the queue is located
    :param str location: The location where the queue is located
    :param str queue: The ID of the queue to add the task to
    :param str url: The target URL of the task
    :param dict json_payload: The JSON payload to send
    :param int scheduled_seconds_from_now: Seconds from now to schedule the task for
    :param str task_id: ID to use for the newly created task
    :param int deadline_in_seconds: The deadline in seconds for task
    :param dict headers: Extra headers to the http request
    :return tasks_v2.Task The newly created task.
    """

    if getattr(settings, "DRW_SILENCE_WEBHOOKS", False):
        return

    # Create a client.
    client = tasks_v2.CloudTasksClient()

    # Construct the task.
    task = tasks_v2.Task(
        http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=url,
            headers={"Content-type": "application/json", **(headers if isinstance(headers, dict) else {})},
            body=json.dumps(json_payload).encode(),
        ),
        name=(client.task_path(project, location, queue, task_id) if task_id is not None else None),
    )

    # Convert "seconds from now" to an absolute Protobuf Timestamp
    if scheduled_seconds_from_now is not None:
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=scheduled_seconds_from_now)
        )
        task.schedule_time = timestamp

    # Convert "deadline in seconds" to a Protobuf Duration
    if deadline_in_seconds is not None:
        duration = duration_pb2.Duration()
        duration.FromSeconds(deadline_in_seconds)
        task.dispatch_deadline = duration

    # Use the client to send a CreateTaskRequest.
    return client.create_task(
        tasks_v2.CreateTaskRequest(
            # The queue to add the task to
            parent=client.queue_path(project, location, queue),
            # The task itself
            task=task,
        )
    )
