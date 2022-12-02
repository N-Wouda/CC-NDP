from dataclasses import dataclass

import numpy as np

from .Node import Node


@dataclass(frozen=True)
class SourceNode(Node):
    """
    Represents a source node in the model graph.
    """

    supply: np.array

    def __str__(self) -> str:
        return f"source[{self.idx}]"
