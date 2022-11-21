from gurobipy import MConstr, MVar

from .MasterProblem import MasterProblem
from .SubProblem import SubProblem


class BB(SubProblem):
    """
    Basic Benders formulation.

    The model looks something like this:

        min  sum(s)
        s.t. Wf - Is <= h - Tx
                f, s >= 0

    given variables x from the master problem. Any keyword arguments are passed
    to the Gurobi model as parameters.
    """

    def _set_vars(self, master: MasterProblem) -> MVar:
        pass

    def _set_constrs(self, master: MasterProblem) -> MConstr:
        pass
