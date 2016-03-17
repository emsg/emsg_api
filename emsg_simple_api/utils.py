import types
from django.db import models
import json
from django.core.serializers.json import DateTimeAwareJSONEncoder
from decimal import *
from django.forms.models import model_to_dict


def json_encode(data):
    def _any(data):
        if isinstance(data, models.Model):
            ret = model_to_dict(data)
        else:
            ret = data
        return ret
    ret = _any(data)
    return json.dumps(ret, cls=DateTimeAwareJSONEncoder)

