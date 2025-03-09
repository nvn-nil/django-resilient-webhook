from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import Signal

from django_resilient_webhook.utilities.model_serializer import serialize_model_data


# from django_resilient_webhook.models import Webhook
# from django.dispatch import receiver


drw_event_receive = Signal()
drw_event_parse_success = Signal()
drw_event_parse_fail = Signal()


def save_webhookable_subclass(created, **kwargs):
    if created:
        create_webhookable_subclass(created=created, **kwargs)
    else:
        update_webhookable_subclass(created=created, **kwargs)


def trigger_webhook(webhooks, label, data):
    for webhook in webhooks:
        webhook.post(label, data, headers=None)


def create_webhookable_subclass(instance, **kwargs):
    # TODO: Handle 'create' event properly
    # NOTE: Create does not trigger because 'webhook' is a reverse relation and cannot
    # be directly assigned when creating webhookable mode instance
    # This means we need to create the webhookable mode instance first before assigining
    # webhook to it. So, the object already exists at the time.
    serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
    trigger_webhook(instance.webhooks.all(), "create", serialized_data)


def update_webhookable_subclass(instance, **kwargs):
    serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
    trigger_webhook(instance.webhooks.all(), "update", serialized_data)


def delete_webhookable_subclass(instance, **kwargs):
    serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
    trigger_webhook(instance.webhooks.all(), "delete", serialized_data)


def connect_signals_to_class(cls):
    post_save.connect(save_webhookable_subclass, sender=cls, weak=False)
    post_delete.connect(delete_webhookable_subclass, sender=cls, weak=False)
    m2m_changed.connect(save_webhookable_subclass, sender=cls, weak=False)


# @receiver(pre_save, sender=Webhook)
# def webhook_pre_save(instance, **kwargs):
#     instance.__content_object = Webhook.objects.get(pk=instance.id).content_object if instance.id else None


# @receiver(post_save, sender=Webhook)
# def webhook_post_save(instance, **kwargs):
#     # NOTE: This is a workaround for 'eventual consistency' with creation. We cannot trigger the 'create'
#     # event webhook because of reasons mentioned in create_webhookable_subclass method notes.
#     # As a hackish solution, we trigger the create event when a webhook is assigned a a content_object
#     # We can assume the moment the object is assigned to a webhook to be creation of the resources w.r.t
#     # the webhook alerted service.
#     # NOTE: This might mean that duplicate model instance create events can be triggered if webhook changes
#     if instance.__content_object != instance.content_object and instance.content_object:
#         serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
#         trigger_webhook(instance.webhooks.all(), "create", serialized_data)
