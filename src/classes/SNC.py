import numpy as np
from gurobipy import Constr, Var
from scipy.sparse import hstack

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

    def _set_vars(self, master: MasterProblem) -> list[Var]:
        nrow, ncol = self._W.shape
        self._f = self._model.addMVar((ncol,)).tolist()
        self._s = [self._model.addVar(obj=1, name="s")]

        return self._f + self._s

    def _set_constrs(self, master: MasterProblem) -> list[Constr]:
        one = np.ones((self._T.shape[0], 1))

        return self._model.addMConstrs(
            hstack([self._W, one]), None, self._senses, self._h
        )
