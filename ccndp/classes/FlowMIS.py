import numpy as np
from gurobipy import Constr
from scipy.sparse import hstack

from .SNC import SNC


class FlowMIS(SNC):
    """
    FlowMIS formulation based on SNC. The slack is inserted only into the
    demand constraints, that is, constraints whose names start with "demand".
    """

    def _set_constrs(self) -> list[Constr]:
        demands = np.array([name.startswith("demand") for name in self._cname])
        demands = demands[..., np.newaxis]

        return self._model.addMConstrs(
            hstack([self._W, demands]), None, self._senses, self._h
        )
