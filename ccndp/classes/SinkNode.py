from dataclasses import dataclass

import numpy as np

from .Node import Node
from .Resource import Resource


@dataclass(frozen=True)
class SinkNode(Node):
    """
    Represents a sink node in the model graph.
    """

    needs: Resource  # the resource demanded at this sink
    demand: np.array  # demands at this sink, indexed by scenario

    def __str__(self) -> str:
        return f"sink[{self.idx}]"
