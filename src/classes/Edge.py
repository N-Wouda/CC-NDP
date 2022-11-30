from dataclasses import dataclass

from .Node import Node


@dataclass(frozen=True)
class Edge:
    frm: Node
    to: Node
    cost: float
    vtype: str

    def __str__(self) -> str:
        if self.frm == self.to:
            # Is some sort of facility, starting and ending in the same point.
            return self.frm.name

        return f"({self.frm.name, self.to.name})"
