from __future__ import annotations

from dataclasses import dataclass


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
    """

    idx: int
    loc: tuple[float, float]

    def __eq__(self, other):
        return isinstance(other, Node) and self.idx == other.idx

    def __str__(self) -> str:
        return f"node[{self.idx}]"
