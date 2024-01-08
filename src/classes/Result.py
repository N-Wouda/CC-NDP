from __future__ import annotations

import json
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np

from .JsonDecoder import JsonDecoder
from .JsonEncoder import JsonEncoder


@dataclass
class Result:
    decisions: dict[str, float]  # (near) optimal first-stage decisions
    decision_costs: dict[str, float]  # costs of the first-stage decisions
    bounds: list[float]  # list of lower bounds
    objectives: list[float]  # list of objectives
    run_times: list[float]  # wall-time (seconds) per iteration
    is_optimal: bool = True  # is the solution optimal?

    def __post_init__(self):
        # This reduces the resulting file size considerably, without impacting
        # the actual results too much (two decimal precision is plenty for our
        # uses). The decisions and decision costs already have one or two
        # decimal precision, so we do not need to touch those here.
        self.bounds = [round(bnd, 2) for bnd in self.bounds]
        self.objectives = [round(obj, 2) for obj in self.objectives]
        self.run_times = [round(run_time, 2) for run_time in self.run_times]

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

    @classmethod
    def from_file(cls, loc: str, decoder=JsonDecoder) -> "Result":
        """
        Reads an object from the given location. Assumes the data at the given
        location are JSON-formatted.
        """
        with open(loc, "r") as fh:
            raw = json.load(fh, cls=decoder)

        return cls(**raw)  # type: ignore

    def to_file(self, loc: str, encoder=JsonEncoder):
        """
        Writes this object as JSON to the given location on the filesystem.
        """
        with open(loc, "w") as fh:
            json.dump(vars(self), fh, cls=encoder)

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
            b, c = np.polyfit(x, self.run_times, 1)
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
