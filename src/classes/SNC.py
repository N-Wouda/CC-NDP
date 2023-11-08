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
        _, ncol = self.W.shape
        f = self.model.addMVar((ncol,)).tolist()
        s = [self.model.addVar(obj=1, name="s")]

        return f + s

    def _set_constrs(self) -> list[Constr]:
        sense2sign = {">": 1, "<": -1, "=": 0}
        one = np.array([sense2sign[sense] for sense in self.senses])
        one.shape = (len(one), 1)

        return self.model.addMConstr(
            hstack([self.W, one]), None, self.senses, self.h
        ).tolist()
