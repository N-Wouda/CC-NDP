import logging

import numpy as np
from gurobipy import GRB, LinExpr, Model

from .Cut import Cut
from .Result import Result
from .SubProblem import SubProblem

logger = logging.getLogger(__name__)


class MasterProblem:
    """
    Master problem formulation.

    TODO
    """

    def __init__(self):
        pass

    def add_lazy_cut(self, cut: Cut):
        lhs = LinExpr()
        lhs.addTerms(cut.gamma, self._z[cut.scen])  # type: ignore
        lhs.addTerms(cut.beta, self._x)  # type: ignore

        self._model.cbLazy(lhs >= cut.gamma)

    def solve_decomposition(self, subproblems: list[SubProblem]) -> Result:
        run_times = []
        lower_bounds = []
        incumbent_objs = []

        def callback(model: Model, where: int):
            if where != GRB.Callback.MIPSOL:
                return

            obj = model.cbGet(GRB.Callback.MIPSOL_OBJ)
            bnd = model.cbGet(GRB.Callback.MIPSOL_OBJBND)

            logger.info(f"MIPSOL: obj. {obj:.2f}, bnd. {bnd:.2f}.")

            lower_bounds.append(bnd)
            incumbent_objs.append(obj)
            run_times.append(model.cbGet(GRB.Callback.RUNTIME))

            x = np.array(model.cbGetSolution(self._x))
            z = np.array(model.cbGetSolution(self._z), dtype=np.int)

            for z_i, sub in zip(z, subproblems):
                if z_i == 1:  # scenario is not selected, so is allowed to be
                    continue  # infeasible in this iteration.

                sub.update_rhs(x)
                sub.solve()

                if not sub.is_feasible():
                    self.add_lazy_cut(sub.cut())

        self.model.optimize(callback)  # type: ignore

        return Result(dict(zip(self.decision_names(), self.decisions())),
                      dict(zip(self.decision_names(), self.c)),
                      lower_bounds,
                      incumbent_objs,
                      np.diff(run_times, prepend=0))  # type: ignore
