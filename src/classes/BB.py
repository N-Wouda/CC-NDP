from gurobipy import Constr, Var
from scipy.sparse import eye, hstack

from .MasterProblem import MasterProblem
from .SubProblem import SubProblem


class BB(SubProblem):
    """
    Basic Benders formulation.

    The model looks something like this:

        min  sum(s)
        s.t. Wf - Is <= h - Tx
                f, s >= 0

    given variables x from the master problem. Here, s is a vector of slacks,
    one for each constraint.

    Any keyword arguments are passed to the Gurobi model as parameters.
    """

    def _set_vars(self, master: MasterProblem) -> list[Var]:
        nrow, ncol = self._W.shape
        self._f = self._model.addMVar((ncol,), name="f").tolist()
        self._s = self._model.addMVar((nrow,), obj=1, name="s").tolist()

        return self._f + self._s

    def _set_constrs(self, master: MasterProblem) -> list[Constr]:
        return self._model.addMConstr(
            hstack([self._W, eye(self._W.shape[0])]),
            None,
            self._senses,
            self._h,
        )
