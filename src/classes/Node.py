from dataclasses import dataclass


@dataclass(frozen=True)
class Node:
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
