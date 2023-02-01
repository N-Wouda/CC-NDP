from dataclasses import dataclass

from ccndp.utils import JsonStorableMixin


@dataclass
class RootResult(JsonStorableMixin):
    """
    Stores data related to the progress made at the root node of the master
    problem's branch and bound tree.
    """

    lp_run_time: float
    lp_objective: float
    mip_run_time: float
    mip_objective: float

    def __str__(self):
        lines = [
            "Root results",
            "============",
            f"       LP objective: {self.lp_objective:.2f}",
            f"      MIP objective: {self.mip_objective:.2f}",
            f" LP run-time (wall): {self.lp_run_time:.2f}s",
            f"MIP run-time (wall): {self.mip_run_time:.2f}s",
        ]

        return "\n".join(lines)
