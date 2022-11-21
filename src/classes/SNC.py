from gurobipy import MConstr, MVar

from .MasterProblem import MasterProblem
from .SubProblem import SubProblem


class SNC(SubProblem):
    """
    Standard normalisation condition (SNC) of Balas 1997.

    The model looks something like this:

        min  s
        s.t. Wf - s1 <= h - Tx
                f, s >= 0,

    where s is a scalar variable.
    """

    def _set_vars(self, master: MasterProblem) -> MVar:
        pass

    def _set_constrs(self, master: MasterProblem) -> MConstr:
        pass
