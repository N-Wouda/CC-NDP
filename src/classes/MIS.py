import numpy as np
from gurobipy import Constr
from scipy.sparse import hstack

from .SNC import SNC


class MIS(SNC):
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

    def _set_constrs(self) -> list[Constr]:
        one = -np.ones((self.T.shape[0], 1))
        one[np.isclose(self.T.sum(axis=1), 0.0)] = 0

        return self.model.addMConstr(
            hstack([self.W, one]), None, self.senses, self.h
        ).tolist()
