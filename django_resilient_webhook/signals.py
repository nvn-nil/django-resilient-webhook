from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import Signal


drw_event_receive = Signal()
drw_event_parse_success = Signal()
drw_event_parse_fail = Signal()


def save_webhookable_subclass(created, **kwargs):
    if created:
        create_webhookable_subclass(created=created, **kwargs)
    else:
        update_webhookable_subclass(created=created, **kwargs)


def create_webhookable_subclass(**kwargs):
    print("create_handler", kwargs)


def update_webhookable_subclass(**kwargs):
    print("update_handler", kwargs)
    pass


def delete_webhookable_subclass(**kwargs):
    print("delete_handler", kwargs)
    pass


def connect_signals_to_class(cls):
    post_save.connect(save_webhookable_subclass, sender=cls, weak=False)
    post_delete.connect(delete_webhookable_subclass, sender=cls, weak=False)
    m2m_changed.connect(save_webhookable_subclass, sender=cls, weak=False)
