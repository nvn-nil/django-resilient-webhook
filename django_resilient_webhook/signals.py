from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import Signal

from django_resilient_webhook.utilities.model_serializer import serialize_model_data


drw_event_receive = Signal()
drw_event_parse_success = Signal()
drw_event_reject = Signal()
drw_event_discard = Signal()


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


def get_model_webhooks(instance):
    from django_resilient_webhook.models import Webhook

    webhooks = Webhook.objects.filter(label=instance.__class__.__name__.lower(), active=True)
    return webhooks


def trigger_webhook(webhooks, label, data):
    for webhook in webhooks:
        if webhook.active:
            webhook.post(label, data, headers=None)


def create_webhookable_subclass(instance, **kwargs):
    serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
    webhooks = instance.webhooks.all().union(get_model_webhooks(instance), all=False)

    # TODO: Handle 'create' event properly
    # NOTE: Create does not trigger because 'webhook' is a reverse relation and cannot
    # be directly assigned when creating webhookable mode instance
    # This means we need to create the webhookable mode instance first before assigining
    # webhook to it. So, the object already exists at the time.
    trigger_webhook(kwargs.get("webhooks", webhooks), "create", serialized_data)

    create_prefixed_events = [event.split(":")[1] for event in instance.WEBHOOK_EVENTS if event.startswith("create:")]
    for event_handler_name in create_prefixed_events:
        if hasattr(instance, event_handler_name):
            event_handler_attr = getattr(instance, event_handler_name)
            if callable(event_handler_attr):
                event_handler_attr(instance=instance, **kwargs)


def update_webhookable_subclass(instance, **kwargs):
    serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
    webhooks = instance.webhooks.all().union(get_model_webhooks(instance), all=False)
    trigger_webhook(kwargs.get("webhooks", webhooks), "update", serialized_data)

    create_prefixed_events = [event.split(":")[1] for event in instance.WEBHOOK_EVENTS if event.startswith("update:")]
    for event_handler_name in create_prefixed_events:
        if hasattr(instance, event_handler_name):
            event_handler_attr = getattr(instance, event_handler_name)
            if callable(event_handler_attr):
                event_handler_attr(instance=instance, **kwargs)


def delete_webhookable_subclass(instance, **kwargs):
    serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
    webhooks = instance.webhooks.all().union(get_model_webhooks(instance), all=False)
    trigger_webhook(kwargs.get("webhooks", webhooks), "delete", serialized_data)

    create_prefixed_events = [event.split(":")[1] for event in instance.WEBHOOK_EVENTS if event.startswith("delete:")]
    for event_handler_name in create_prefixed_events:
        if hasattr(instance, event_handler_name):
            event_handler_attr = getattr(instance, event_handler_name)
            if callable(event_handler_attr):
                event_handler_attr(instance=instance, **kwargs)


def connect_signals_to_class(cls):
    post_save.connect(save_webhookable_subclass, sender=cls, weak=False)
    pre_delete.connect(delete_webhookable_subclass, sender=cls, weak=False)
    m2m_changed.connect(save_webhookable_subclass, sender=cls.webhooks.through, weak=False)
