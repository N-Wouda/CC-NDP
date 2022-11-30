from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
    """
    Represents a node in the model graph.

    This class stores the node's name (useful alias), its location in the plain
    as an (x, y) tuple, and whether this node is a source or a sink in the
    model graph.
    """

    name: str
    loc: tuple[float, float]
    is_source: bool
    is_sink: bool

    # TODO node type (sum/assembly)
    # TODO eta?
    # TODO node number/index?

    def __post_init__(self):
        if self.is_sink and self.is_source:
            raise ValueError("Cannot be sink *and* source.")

    def __str__(self) -> str:
        return self.name
