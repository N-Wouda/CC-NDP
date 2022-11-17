from abc import ABC

import numpy as np

from .Cut import Cut


class SubProblem(ABC):
    """
    Abstract base class for a subproblem formulation.
    """

    def __init__(self):
        pass

    def cut(self) -> Cut:
        pass

    def is_feasible(self) -> bool:
        pass

    def objective(self) -> float:
        pass

    def solve(self):
        pass

    def update_rhs(self, x: np.ndarray):
        pass
