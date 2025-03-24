import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import ManyToManyField, Model


class SerializationError(Exception):
    """Raised when required fields are missing in the model."""

    def __init__(self, missing_fields=None, failing_properties=None):
        message = ""
        if missing_fields:
            message = f"Missing fields: {', '.join(missing_fields)}"
            self.missing_fields = missing_fields
        if failing_properties:
            message += f"Failing properties: {', '.join(failing_properties)}"
            self.failing_properties = failing_properties
        super().__init__(message)


def serialize_model_data(instance: Model, fields: list[str], include_properties=True, skip_methods=True):
    """Serializes selected fields from a Django model instance, including M2M & related fields.

    :param Model instance: Django model instance to serialize
    :param list[str] fields: List of fields to serialize (supports `related__field` syntax)
    :param bool include_properties: Whether to include @property or cached_property fields
    :param bool skip_methods: Whether to call attributes if they're callable
    :raises SerializationError: If required fields are missing

    :return dict:Serialized model data
    """
    data = {}
    model_class = instance.__class__
    missing_fields = []
    failing_fields = []

    for field in fields:
        if "__" in field:
            # Handle related fields (ForeignKey, ManyToMany)
            relation, sub_field = field.split("__", 1)

            if not hasattr(instance, relation):
                missing_fields.append(relation)
                continue

            related_attr = getattr(instance, relation, None)

            if isinstance(getattr(model_class, relation).field, ManyToManyField) or hasattr(related_attr, "all"):
                # Handle ManyToManyField as a list of values
                data[field] = [getattr(obj, sub_field, None) for obj in related_attr.all()]
            else:
                # Handle ForeignKey fields
                if not related_attr or not hasattr(related_attr, sub_field):
                    missing_fields.append(field)
                else:
                    data[field] = getattr(related_attr, sub_field, None)

        else:
            if hasattr(instance, field):
                attr = getattr(instance, field)
                if callable(attr) and skip_methods:
                    continue
                elif callable(attr):
                    data[field] = attr()
                else:
                    data[field] = attr
            elif include_properties and hasattr(model_class, field):
                prop = getattr(model_class, field)
                if isinstance(prop, property):
                    try:
                        data[field] = getattr(instance, field)  # Evaluate property
                    except Exception:
                        data[field] = None  # Skip failing properties
                        failing_fields.append(field)
                else:
                    missing_fields.append(field)
            else:
                missing_fields.append(field)

    if missing_fields:
        raise SerializationError(missing_fields=missing_fields, failing_properties=failing_fields)

    return {
        "model": str(instance._meta),
        "pk": str(instance.id),
        "fields": json.loads(json.dumps(data, cls=DjangoJSONEncoder)),
    }
