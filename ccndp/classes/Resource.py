from dataclasses import dataclass


@dataclass
class Resource:
    """
    Represents a resource type, identified by a name. These resources are
    produced at nodes, and serve as inputs for downstream processes.
    """

    name: str

    def __str__(self) -> str:
        return self.name
