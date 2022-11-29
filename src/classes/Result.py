from dataclasses import dataclass

import numpy as np

from src.utils import JsonStorableMixin


@dataclass
class Result(JsonStorableMixin):
    decisions: dict[str, float]  # (near) optimal first-stage decisions
    decision_costs: dict[str, float]  # costs of the first-stage decisions
    bounds: list[float]  # list of lower bounds
    objectives: list[float]  # list of objectives
    run_times: list[float]  # wall-time (seconds) per iteration
    is_optimal: bool = True  # is the solution optimal?

    @property
    def lower_bound(self) -> float:
        return self.bounds[-1]

    @property
    def num_iters(self) -> int:
        return len(self.bounds)

    @property
    def objective(self) -> float:
        return self.objectives[-1]

    @property
    def run_time(self) -> float:
        """
        Total run-time (wall-time, in seconds) for the entire algorithm.
        """
        return sum(self.run_times)

    def __str__(self):
        summary = [
            "Solution results",
            "================",
            f"   # iterations: {self.num_iters}",
            f"      objective: {self.objective:.2f}",
            f"    lower bound: {self.lower_bound:.2f}",
            f"run-time (wall): {self.run_time:.2f}s",
            f"        optimal? {self.is_optimal}\n",
        ]

        decisions = [
            "Decisions",
            "=========",
            "(only non-zero decisions)\n",
        ]

        for var, value in self.decisions.items():
            if not np.isclose(value, 0.0):
                decisions.append(f"{var:>32}: {value:.2f}")

        return "\n".join(summary + decisions)
