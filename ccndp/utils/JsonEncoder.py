import json

import numpy as np

from ccndp.classes.Edge import Edge


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        if isinstance(obj, np.generic):
            return obj.item()

        data = vars(obj)

        if isinstance(obj, Edge):
            data["frm"] = obj.frm.idx
            data["to"] = obj.to.idx

        return data
