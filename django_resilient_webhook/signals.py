import logging

from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import Signal

from django_resilient_webhook.utilities.model_serializer import serialize_model_data


logger = logging.getLogger(__name__)

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


def unified_signal_handler(event_label, instance, **kwargs):
    if event_label in instance.WEBHOOK_EVENTS:
        serialized_data = serialize_model_data(instance, instance.WEBHOOK_SERIALIZED_FIELDS)
        webhooks = instance.webhooks.all().union(get_model_webhooks(instance), all=False)

        trigger_webhook(kwargs.get("webhooks", webhooks), event_label, serialized_data)

        sideffect_events = [
            event.split(":")[1] for event in instance.WEBHOOK_EVENTS if event.startswith(f"{event_label}:")
        ]
        for event_handler_name in sideffect_events:
            if hasattr(instance, event_handler_name):
                event_handler_attr = getattr(instance, event_handler_name)
                if callable(event_handler_attr):
                    event_handler_attr(instance=instance, **kwargs)
                else:
                    logger.warning("%s %s is not a callable", instance.__class__.__name__, event_handler_name)
            else:
                logger.warning("%s does not define %s as a callable", instance.__class__.__name__, event_handler_name)


def create_webhookable_subclass(instance, **kwargs):
    # NOTE: Create does not trigger because 'webhook' is a reverse relation and cannot
    # be directly assigned when creating webhookable mode instance
    # 'create' can only be triggered by a modelname labelled Webhook with a 'create' labeled endpoint
    unified_signal_handler("create", instance, **kwargs)


def update_webhookable_subclass(instance, **kwargs):
    unified_signal_handler("update", instance, **kwargs)


def delete_webhookable_subclass(instance, **kwargs):
    unified_signal_handler("delete", instance, **kwargs)


def connect_signals_to_class(cls):
    post_save.connect(save_webhookable_subclass, sender=cls, weak=False)
    pre_delete.connect(delete_webhookable_subclass, sender=cls, weak=False)
    m2m_changed.connect(save_webhookable_subclass, sender=cls.webhooks.through, weak=False)
