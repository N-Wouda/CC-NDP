from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    """
    Represents a node in the model graph.

    This class stores the node's idx and its location in the plain as an (x, y)
    tuple.
    """

    idx: int
    loc: tuple[float, float]

    # TODO properties: (here, or on edges?)
    #  - node type (sum/assembly)
    #  - eta?

    def __str__(self) -> str:
        return f"facility[{self.idx}]"
