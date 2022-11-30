from dataclasses import dataclass

from .Node import Node


@dataclass(frozen=True)
class Edge:
    frm: Node
    to: Node
    cost: float
    vtype: str

    def __str__(self) -> str:
        return f"({self.frm, self.to})"
