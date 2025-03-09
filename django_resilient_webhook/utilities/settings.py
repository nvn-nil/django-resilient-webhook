from django.conf import settings


def parse_queue_setting():
    queue_path = settings.DRW_GCP_WEBHOOK_QUEUE_PATH

    queue_path = queue_path.replace("projects/", "") if queue_path.startswith("projects/") else queue_path

    print("queue_path", queue_path.split("/"))

    project_id, _, location, _, queue_id = queue_path.split("/")
    return {"project_id": project_id, "location": location, "queue_id": queue_id}
