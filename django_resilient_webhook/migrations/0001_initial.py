# Generated by Django 4.2.19 on 2025-03-09 18:42

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Endpoint",
            fields=[
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, help_text="Datetime the Endpoint was created"),
                ),
                (
                    "last_modified",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Datetime of the last modification of the Endpoint",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        help_text="Universally Unique ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("url", models.TextField(help_text="URL to an post-able endpoint")),
                (
                    "label",
                    models.SlugField(
                        help_text="Identifier for this endpoint. Labels 'create', 'update', and 'delete' will be connected to model lifecycle"
                    ),
                ),
                (
                    "data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="If provided, this data will be passed in along with the payload",
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Webhook",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("version", models.CharField(max_length=64)),
                (
                    "endpoints",
                    models.ManyToManyField(
                        help_text="Select endpoints for this integration",
                        to="django_resilient_webhook.endpoint",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DispatchEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        help_text="Universally Unique ID",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "dispatched",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Datetime the Endpoint was dispatched",
                    ),
                ),
                (
                    "payload",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="If provided, data posted to the endpoint",
                        null=True,
                    ),
                ),
                ("task_name", models.CharField(max_length=255)),
                (
                    "endpoint",
                    models.ForeignKey(
                        help_text="The webhook endpoint which was dispactched",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispatch_events",
                        to="django_resilient_webhook.endpoint",
                    ),
                ),
                (
                    "webhook",
                    models.ForeignKey(
                        blank=True,
                        help_text="The Webhook through which the endpoint was dispactched",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dispatch_events",
                        to="django_resilient_webhook.webhook",
                    ),
                ),
            ],
        ),
    ]
