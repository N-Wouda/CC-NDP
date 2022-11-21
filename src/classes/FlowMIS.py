from gurobipy import MConstr

from .MasterProblem import MasterProblem
from .SNC import SNC


class FlowMIS(SNC):
    """
    FlowMIS formulation based on SNC. The slack is inserted only into the
    demand constraint.
    """

    def _set_constrs(self, master: MasterProblem) -> MConstr:
        pass
