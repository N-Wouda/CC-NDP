from dataclasses import dataclass

import numpy as np

from .Node import Node


@dataclass(frozen=True)
class SinkNode(Node):
    """
    Represents a sink node in the model graph.
    """

    demand: np.array

    def __str__(self) -> str:
        return f"sink[{self.idx}]"
