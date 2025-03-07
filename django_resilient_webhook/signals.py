import django.dispatch


drw_event_receive = django.dispatch.Signal()
drw_event_parse_success = django.dispatch.Signal()
drw_event_parse_fail = django.dispatch.Signal()
