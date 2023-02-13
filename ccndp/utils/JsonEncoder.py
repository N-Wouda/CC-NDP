import json

import numpy as np

from ccndp.classes.Edge import Edge


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        if isinstance(obj, np.generic):
            return obj.item()

        if isinstance(obj, Edge):
            obj.frm = obj.frm.idx
            obj.to = obj.to.idx

        return vars(obj)
