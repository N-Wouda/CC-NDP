from __future__ import annotations

from dataclasses import dataclass

from .Node import Node
from .Resource import Resource


@dataclass(frozen=True)
class FacilityNode(Node):
    """
    Represents a facility node in the model graph.
    """

    makes: Resource  # the resource made by this facility
    needs: tuple[Resource, ...]  # the inputs required by this facility

    # TODO properties:
    #  - conversion factor (here or on edges?)

    def __eq__(self, other):
        return isinstance(other, Node) and self.idx == other.idx

    def __str__(self) -> str:
        return f"facility[{self.idx}]"
