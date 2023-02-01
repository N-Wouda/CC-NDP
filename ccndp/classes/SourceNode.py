from dataclasses import dataclass

import numpy as np

from .Node import Node


@dataclass(frozen=True)
class SourceNode(Node):
    """
    Represents a source node in the model graph.
    """

    supply: np.array

    def __eq__(self, other):
        return isinstance(other, SourceNode) and str(other) == str(self)

    def __str__(self) -> str:
        return f"source[{self.idx}]"
