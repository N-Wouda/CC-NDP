from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    """
    Represents a node in the model graph.

    This class stores the node's idx and its location in the plain as an (x, y)
    tuple, along with information about the type of node it is.
    """

    idx: int
    loc: tuple[float, float]
    node_type: str

    def __post_init__(self):
        if self.node_type not in ["SUM", "MIN"]:
            raise ValueError("node_type must be one of [SUM, MIN]")

    # TODO properties: (here, or on edges?)
    #  - eta?

    def __eq__(self, other):
        return isinstance(other, Node) and self.idx == other.idx

    def __str__(self) -> str:
        return f"facility[{self.idx}]"
