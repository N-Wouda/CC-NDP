from dataclasses import dataclass
from functools import cache, cached_property

import numpy as np

from src.utils import JsonStorableMixin


@dataclass
class ProblemData(JsonStorableMixin):
    """
    Problem data instance.

    Parameters
    ----------
    nodes
        Array of node names.
    locs
        Array of node locations, as (x, y) pairs.
    edges
        Array of edges, as (from, to) node strings.
    demand
        Array of scenario demands. Rows are scenarios, columns each sink
        demand.
    capacity
        Array of edge capacities. Rows are scenarios, columns each edge
        capacity.
    cost
        Array of edge construction costs.
    vtype
        Array of edge construction types. Can be one of 'C', 'B', or 'I'.
    num_scenarios
        Number of scenarios to consider.
    """

    nodes: np.ndarray
    locs: np.ndarray
    edges: np.ndarray
    demand: np.ndarray
    capacity: np.ndarray
    cost: np.ndarray
    vtype: np.ndarray
    num_scenarios: int

    # TODO eta?
    # TODO node type?

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    @cached_property
    def sink_nodes(self) -> list[str]:
        """
        Returns all nodes that have no edges leaving them.
        """
        return [
            node for node in self.nodes if not self.edge_idcs_from_node(node)
        ]

    @cache
    def edge_idcs_from_node(self, node: str) -> list[int]:
        return [idx for idx, edge in enumerate(self.edges) if edge[0] == node]

    @cache
    def edge_idcs_to_node(self, node: str) -> list[int]:
        return [idx for idx, edge in enumerate(self.edges) if edge[1] == node]
