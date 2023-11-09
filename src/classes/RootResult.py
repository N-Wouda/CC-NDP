import json
from dataclasses import dataclass

from .JsonEncoder import JsonEncoder


@dataclass
class RootResult:
    """
    Stores data related to the progress made at the root node of the master
    problem's branch and bound tree.
    """

    lp_run_time: float
    lp_objective: float
    mip_run_time: float
    mip_objective: float

    def to_file(self, loc: str, encoder=JsonEncoder):
        """
        Writes this object as JSON to the given location on the filesystem.
        """
        with open(loc, "w") as fh:
            json.dump(vars(self), fh, cls=encoder)

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
