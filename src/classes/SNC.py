import numpy as np
from gurobipy import Constr, Var
from scipy.sparse import hstack

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

    def _set_vars(self) -> list[Var]:
        nrow, ncol = self._W.shape
        f = self._model.addMVar((ncol,)).tolist()
        s = [self._model.addVar(obj=1, name="s")]

        return f + s

    def _set_constrs(self) -> list[Constr]:
        sense2sign = {">": 1, "<": -1, "=": 0}
        one = np.array([sense2sign[sense] for sense in self._senses])
        one.shape = (len(one), 1)

        return self._model.addMConstrs(
            hstack([self._W, one]), None, self._senses, self._h
        )
