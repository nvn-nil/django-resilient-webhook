from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import Signal

from django_resilient_webhook.utilities.model_serializer import serialize_model_data


drw_event_receive = Signal()
drw_event_parse_success = Signal()
drw_event_parse_fail = Signal()


def save_webhookable_subclass(**kwargs):
    has_created_kwarg = "created" in kwargs
    if has_created_kwarg and kwargs["created"]:
        create_webhookable_subclass(**kwargs)
    elif has_created_kwarg and not kwargs["created"]:
        update_webhookable_subclass(**kwargs)
    elif not has_created_kwarg:
        if hasattr(kwargs["instance"], "webhooks"):
            # This is m2m_changed
            # NOTE: We will use m2m_changed to notify when webhook is assigned to an object
            # This can be used as a 'create' (pseudo) event w.r.t an external service
            # print("in 3rd case", kwargs, kwargs["instance"], kwargs["instance"].webhooks.all())
            #
            # We cannot assume removing a webhook to be deletion so do nothing then

            if kwargs["action"] == "pre_clear":
                # Do not do anything when the m2m relation is removed
                # print("pre_clear", kwargs["instance"].webhooks.all(), kwargs["pk_set"])
                pass
            elif kwargs["action"] == "post_add":
                added_webhookes = kwargs["instance"].webhooks.filter(pk__in=kwargs["pk_set"])
                create_webhookable_subclass(instance=kwargs["instance"], webhooks=added_webhookes)
            elif kwargs["action"] == "pre_remove":
                # Do not do anything when the m2m relation is removed
                # print("pre_remove", kwargs["instance"].webhooks.all(), kwargs["pk_set"])
                pass


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
    trigger_webhook(kwargs.get("webhooks", instance.webhooks.all()), "create", serialized_data)


def update_webhookable_subclass(instance, **kwargs):
    serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
    trigger_webhook(kwargs.get("webhooks", instance.webhooks.all()), "update", serialized_data)


def delete_webhookable_subclass(instance, **kwargs):
    serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
    trigger_webhook(kwargs.get("webhooks", instance.webhooks.all()), "delete", serialized_data)


def connect_signals_to_class(cls):
    post_save.connect(save_webhookable_subclass, sender=cls, weak=False)
    pre_delete.connect(delete_webhookable_subclass, sender=cls, weak=False)
    m2m_changed.connect(save_webhookable_subclass, sender=cls.webhooks.through, weak=False)


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
