import json

from django.core import serializers


def serialize_model_data(instance, fields):
    serialize_fields = fields if fields else []

    serialized_data_str = serializers.serialize("json", [instance], fields=serialize_fields)
    serialized_data = json.loads(serialized_data_str)
    if isinstance(serialized_data, list):
        serialized_data = serialized_data[0]

    return serialized_data
