from dataclasses import dataclass

import numpy as np

from .Node import Node
from .Resource import Resource


@dataclass(frozen=True)
class SourceNode(Node):
    """
    Represents a source node in the model graph.
    """

    makes: Resource  # the resource made by this source
    supply: np.array  # supply at this source, indexed by scenario

    def __str__(self) -> str:
        return f"source[{self.idx}]"
