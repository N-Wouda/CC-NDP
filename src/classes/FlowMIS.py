import numpy as np
from gurobipy import Constr
from scipy.sparse import hstack

from .SNC import SNC


class FlowMIS(SNC):
    """
    FlowMIS formulation based on SNC. The slack is inserted only into the
    destination balance constraints.
    """

    def _set_constrs(self) -> list[Constr]:
        col = np.array([name.startswith("dest") for name in self.cname])
        col = col[..., np.newaxis]

        return self.model.addMConstr(
            hstack([self.W, col]), None, self.senses, self.h
        ).tolist()
