from dataclasses import dataclass

import numpy as np

from .Node import Node


@dataclass(frozen=True)
class Edge:
    """
    Represents an edge in the model graph.

    This class stores the (start, end) nodes that this edge connects, the cost
    of constructing this edge, its (variable) capacity per scenario, and the
    variable type of this edge.
    """

    frm: Node
    to: Node
    cost: float
    capacity: np.array  # capacity per scenario
    vtype: str = "C"

    def __str__(self) -> str:
        if str(self.frm) == str(self.to):
            # Is some sort of facility, starting and ending in the same point.
            return f"{self.frm}"

        return f"{self.frm} -> {self.to}"
