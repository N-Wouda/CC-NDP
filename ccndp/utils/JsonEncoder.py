import json

import numpy as np

from ccndp.classes.Edge import Edge
from ccndp.classes.FacilityNode import FacilityNode
from ccndp.classes.SinkNode import SinkNode
from ccndp.classes.SourceNode import SourceNode


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        if isinstance(obj, np.generic):
            return obj.item()

        return serialize(obj)


def serialize(obj):
    data = vars(obj)

    if isinstance(obj, Edge):
        data["frm"] = obj.frm.idx
        data["to"] = obj.to.idx

    if isinstance(obj, SourceNode):
        data["makes"] = obj.makes.idx

    if isinstance(obj, SinkNode):
        data["needs"] = obj.needs.idx

    if isinstance(obj, FacilityNode):
        data["makes"] = obj.makes.idx
        data["needs"] = [res.idx for res in obj.needs]

    return data
