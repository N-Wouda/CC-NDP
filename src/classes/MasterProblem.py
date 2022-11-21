from __future__ import annotations

import logging

import numpy as np
from gurobipy import GRB, LinExpr, Model
from scipy.sparse import csr_matrix

from src.config import DEFAULT_MASTER_PARAMS

from .Cut import Cut
from .Result import Result
from .SubProblem import SubProblem

logger = logging.getLogger(__name__)


class MasterProblem:
    """
    Master problem formulation.

    The model looks something like:

        min  c x
        s.t.      Ax ~ b
             sum(z) <= alpha N
             x mixed-integer, z binary

    The variables x in this model are passed to the scenario subproblems.

    Any keyword arguments are passed to the Gurobi model as parameters.
    """

    def __init__(
        self,
        c: list[float] | np.array,
        A: csr_matrix,
        b: list[float] | np.array,
        sense: list[str] | np.array,
        vtype: list[str] | np.array,
        lb: list[float] | np.array,
        ub: list[float] | np.array,
        vname: list[str],
        cname: list[str],
        num_scenarios: int,
        **params,
    ):
        logger.info("Creating master problem.")

        self._model = Model("master")

        for param, value in (DEFAULT_MASTER_PARAMS | params).items():
            logger.debug(f"Setting {param} = {value}.")
            self._model.setParam(param, value)

        dec_vars = self._model.addMVar((len(c),), lb, ub, c, vtype).tolist()

        self._x = dec_vars[:-num_scenarios]
        self._z = dec_vars[-num_scenarios:]

        constrs = self._model.addMConstrs(A=A, x=None, sense=sense, b=b)

        for var, name in zip(dec_vars, vname):
            var.varName = name

        for constr, name in zip(constrs, cname):
            constr.constrName = name

        self._model.update()

    @property
    def c(self) -> np.array:
        return np.array([x.obj for x in self._x])

    def decisions(self) -> np.array:
        return np.array([var.x for var in self._x])

    def decision_names(self) -> list[str]:
        return [var.varName for var in self._x]

    def objective(self) -> float:
        assert self._model.status == GRB.OPTIMAL
        return self._model.objVal

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

        return Result(
            dict(zip(self.decision_names(), self.decisions())),
            dict(zip(self.decision_names(), self.c)),
            lower_bounds,
            incumbent_objs,
            np.diff(run_times, prepend=0).tolist(),  # type: ignore
        )
