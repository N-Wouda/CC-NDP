import json

import numpy as np


class NumpyJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        if isinstance(obj, np.generic):
            return obj.item()

        return super().default(obj)
