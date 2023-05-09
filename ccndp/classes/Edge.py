from dataclasses import dataclass
from typing import Optional

import numpy as np

from .Node import Node
from .Resource import Resource


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
    vtype: str = "C"  # default continuous

    @property
    def resource(self) -> Optional[Resource]:
        if hasattr(self.frm, "makes"):
            return self.frm.makes  # type: ignore

        return None

    def __str__(self) -> str:
        if str(self.frm) == str(self.to):
            # Is some sort of facility, starting and ending in the same point.
            return f"{self.frm}"

        return f"{self.frm} -> {self.to}"
