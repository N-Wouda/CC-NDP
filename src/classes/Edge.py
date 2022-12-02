from dataclasses import dataclass

from .Node import Node


@dataclass(frozen=True)
class Edge:
    """
    Represents an edge in the model graph.

    This class stores the (start, end) nodes that this edge connects, the cost
    of constructing this edge, and the variable type of this edge.
    """

    frm: Node
    to: Node
    cost: float
    vtype: str

    def __str__(self) -> str:
        if self.frm == self.to:
            # Is some sort of facility, starting and ending in the same point.
            return str(self.frm)

        return f"({self.frm}, {self.to})"
