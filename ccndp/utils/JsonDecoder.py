import json
from functools import partial
from typing import Any, Dict

import numpy as np

# TODO figure out why this does not work without explicit imports
from ccndp.classes.Edge import Edge
from ccndp.classes.FacilityNode import FacilityNode
from ccndp.classes.Node import Node
from ccndp.classes.Resource import Resource
from ccndp.classes.SinkNode import SinkNode
from ccndp.classes.SourceNode import SourceNode


class JsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs["object_hook"] = object_hook
        super().__init__(*args, **kwargs)


def object_hook(obj: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in obj.items():
        if isinstance(v, list):
            obj[k] = np.array(v)

    if "resources" in obj:
        obj["resources"] = list(map(val2res, obj["resources"]))

    if "nodes" in obj:
        assert "resources" in obj
        func = partial(val2node, resources=obj["resources"])
        obj["nodes"] = list(map(func, obj["nodes"]))

    if "edges" in obj:
        assert "nodes" in obj
        func = partial(val2edge, nodes=obj["nodes"])  # type: ignore
        obj["edges"] = list(map(func, obj["edges"]))

    return obj


def val2node(val: dict, resources) -> Node:
    idx = int(val.pop("idx"))

    x, y = val.pop("loc")
    loc = (float(x), float(y))

    if "supply" in val:
        makes = resources[val["makes"]]
        return SourceNode(idx, loc, makes, val["supply"])

    if "demand" in val:
        needs = resources[val["needs"]]
        return SinkNode(idx, loc, needs, val["demand"])

    if "needs" in val and "makes" in val:
        needs = tuple(resources[idx] for idx in val["needs"])
        makes = resources[val["makes"]]
        return FacilityNode(idx, loc, makes, needs)

    return Node(idx, loc)


def val2edge(val: dict, nodes) -> Edge:
    frm = nodes[val.pop("frm")]
    to = nodes[val.pop("to")]
    return Edge(frm, to, **val)


def val2res(val: dict) -> Resource:
    return Resource(**val)
