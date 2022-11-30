from dataclasses import dataclass

import numpy as np

from src.utils import JsonStorableMixin

from .Edge import Edge
from .Node import Node


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
    demands
        Array of scenario demands. Rows are scenarios, columns each sink
        demand.
    capacities
        Array of edge capacities. Rows are scenarios, columns each edge
        capacity.
    num_scenarios
        Number of scenarios.
    """

    nodes: list[Node]
    edges: list[Edge]
    demands: np.ndarray
    capacities: np.ndarray
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

    def sources(self) -> list[Node]:
        return [node for node in self.nodes if node.is_source]

    def sinks(self) -> list[Node]:
        return [node for node in self.nodes if node.is_sink]
