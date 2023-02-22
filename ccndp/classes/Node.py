from __future__ import annotations

from dataclasses import dataclass

from .Resource import Resource


@dataclass(frozen=True)
class Node:
    """
    Represents a node in the model graph.

    Attributes
    ----------
    idx
        Integer identifying this node. Should be unique across all existing
        nodes.
    loc
        Tuple of (x, y) locations in the plane.
    makes
        Tuple of resources this node produces.
    needs
        Tuple of resources this node requires for production.
    """

    idx: int
    loc: tuple[float, float]
    makes: tuple[Resource, ...]
    needs: tuple[Resource, ...]

    # TODO properties:
    #  - conversion factor? (here, or on edges, or on the resources?)

    def __eq__(self, other):
        return isinstance(other, Node) and self.idx == other.idx

    def __str__(self) -> str:
        return f"facility[{self.idx}]"
