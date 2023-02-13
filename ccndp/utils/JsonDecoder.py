import json
from functools import partial
from typing import Any, Dict

import numpy as np

# TODO figure out why this does not work without explicit imports
from ccndp.classes.Edge import Edge
from ccndp.classes.Node import Node
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

    if "nodes" in obj:
        obj["nodes"] = list(map(val2node, obj["nodes"]))

    if "edges" in obj:
        assert "nodes" in obj
        func = partial(val2edge, nodes=obj["nodes"])
        obj["edges"] = list(map(func, obj["edges"]))

    return obj


def val2node(val: dict) -> Node:
    idx = int(val.pop("idx"))

    x, y = val.pop("loc")
    loc = (float(x), float(y))
    node_type = val.pop("node_type")

    if "supply" in val:
        return SourceNode(idx, loc, node_type, **val)

    if "demand" in val:
        return SinkNode(idx, loc, node_type, **val)

    return Node(idx, loc, node_type)


def val2edge(val: dict, nodes) -> Edge:
    frm = val.pop("frm")
    to = val.pop("to")

    return Edge(nodes[frm], nodes[to], **val)
