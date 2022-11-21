from dataclasses import dataclass

from src.utils import JsonStorableMixin


@dataclass
class Result(JsonStorableMixin):
    decisions: dict[str, float]  # (near) optimal first-stage decisions
    decision_costs: dict[str, float]  # costs of the first-stage decisions
    bounds: list[float]  # list of lower bounds
    objectives: list[float]  # list of objectives
    run_times: list[float]  # wall-time (seconds) per iteration
    is_optimal: bool = True  # is the solution optimal?
