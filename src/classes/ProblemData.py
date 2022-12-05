from dataclasses import dataclass

import numpy as np

from src.utils import JsonStorableMixin

from .Edge import Edge
from .Node import Node
from .SinkNode import SinkNode
from .SourceNode import SourceNode


@dataclass(frozen=True)
class ProblemData(JsonStorableMixin):
    """
    Problem data instance.

    Parameters
    ----------
    nodes
        Array of nodes.
    edges
        Array of edges.
    num_scenarios
        Number of scenarios.
    """

    nodes: list[Node]
    edges: list[Edge]
    num_scenarios: int

    def __hash__(self) -> int:
        """
        Returns a hash based on the size properties of the data instance:
        number of nodes, number of edges, and the number of scenarios.
        """
        return hash((len(self.nodes), len(self.edges), self.num_scenarios))

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    def costs(self) -> np.ndarray:
        return np.array([edge.cost for edge in self.edges])

    def vtypes(self) -> np.ndarray:
        return np.array([edge.vtype for edge in self.edges])

    def edge_indices_from(self, node: Node) -> list[int]:
        return [idx for idx, edge in enumerate(self.edges) if edge.frm == node]

    def edge_indices_to(self, node: Node) -> list[int]:
        return [idx for idx, edge in enumerate(self.edges) if edge.to == node]

    def sources(self) -> list[SourceNode]:
        return [node for node in self.nodes if isinstance(node, SourceNode)]

    def sinks(self) -> list[SinkNode]:
        return [node for node in self.nodes if isinstance(node, SinkNode)]
