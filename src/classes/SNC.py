from gurobipy import MConstr, MVar

from .MasterProblem import MasterProblem
from .SubProblem import SubProblem


class SNC(SubProblem):
    """
    TODO
    """

    def _set_vars(self, master: MasterProblem) -> MVar:
        pass

    def _set_constrs(self, master: MasterProblem) -> MConstr:
        pass
