from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np

from ccndp.utils import JsonStorableMixin


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

    def plot_convergence(self, ax: plt.Axes | None = None):
        """
        Plots the steps towards solution. Should hopefully show convergence.
        """
        if ax is None:
            _, ax = plt.subplots(figsize=(12, 8))

        bounds = np.array(self.bounds)
        num_to_skip = np.count_nonzero(bounds < 0)  # first few are -inf

        times = np.cumsum(self.run_times)[num_to_skip:]

        lb = self.bounds[num_to_skip:]
        curr = self.objectives[num_to_skip:]

        ax.plot(times, lb, "o-", label="Lower bound")
        ax.plot(times, curr, "o-", label="Solution")
        ax.plot(
            times[-1], self.objective, "r*", markersize=18, label="Optimal"
        )

        ax.set_xlim(left=0)

        ax.set_xlabel("Run-time (s)")
        ax.set_ylabel("Objective")
        ax.set_title("Convergence plot")

        ax.legend(
            frameon=False, title=f"N = {len(self.bounds)}", loc="lower right"
        )

        plt.tight_layout()
        plt.draw_if_interactive()

    def plot_runtimes(self, ax: plt.Axes | None = None):
        if ax is None:
            _, ax = plt.subplots(figsize=(12, 4))

        x = 1 + np.arange(self.num_iters)
        ax.plot(x, self.run_times)

        if self.num_iters > 1:
            b, c = np.polyfit(x, self.run_times, 1)  # noqa
            ax.plot(b * x + c)

        ax.set_xlim(left=0)

        ax.set_xlabel("Iteration")
        ax.set_ylabel("Run-time (s)")
        ax.set_title("Run-time per iteration")

        plt.tight_layout()
        plt.draw_if_interactive()

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
            "---------",
            "(only non-zero decisions)\n",
        ]

        for var, value in self.decisions.items():
            if not np.isclose(value, 0.0):
                decisions.append(f"{var:>32}: {value:.2f}")

        return "\n".join(summary + decisions)
