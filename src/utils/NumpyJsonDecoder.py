import json
from typing import Any, Dict

import numpy as np


class NumpyJsonDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        kwargs["object_hook"] = _object_hook
        super().__init__(*args, **kwargs)


def _object_hook(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts any list value in the given obj dictionary to a Numpy array.
    """
    for k, v in obj.items():
        if isinstance(v, list):
            obj[k] = np.array(v)

    return obj
