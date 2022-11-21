from gurobipy import MConstr, MVar

from .MasterProblem import MasterProblem
from .SubProblem import SubProblem


class MIS(SubProblem):
    """
    Minimal infeasible subsystem-type formulation (MIS) of Fischetti et al.
    (2010).

    Model looks something like:

        min  s
        s.t. Wf - s1_T <= h - Tx
                  f, s >= 0,

    where s is a scalar variable, and 1_T is a 0/1 vector of indicators that is
    1 for each non-zero row of T.
    """

    def _set_vars(self, master: MasterProblem) -> MVar:
        pass

    def _set_constrs(self, master: MasterProblem) -> MConstr:
        pass
