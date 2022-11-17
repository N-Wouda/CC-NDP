from dataclasses import dataclass

import numpy as np


@dataclass
class ProblemData:
    nodes: list[int]
    locs: list[tuple[int, int]]

    edges: np.ndarray
    capacity: np.ndarray
    cost: np.ndarray
    vtype: np.ndarray

    num_scenarios: int
    # TODO eta?

    @property
    def num_edges(self) -> int:
        return len(self.edges)
