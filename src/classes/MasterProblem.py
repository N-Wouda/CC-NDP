from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from gurobipy import GRB, LinExpr, Model

from src.config import DEFAULT_MASTER_PARAMS
from src.functions import create_master_model

from .Cut import Cut
from .Result import Result

if TYPE_CHECKING:
    from .ProblemData import ProblemData
    from .SubProblem import SubProblem

logger = logging.getLogger(__name__)


class MasterProblem:
    """
    Master problem formulation. The model looks something like:

        min  c y
        s.t.      Ay ~ b
             sum(z) <= alpha N
             y, z binary

    The variables y in this model are passed to the scenario subproblems.

    Parameters
    ----------
    data
        Problem data instance.
    alpha
        Controls the percentage of scenarios that can be infeasible: at least
        (1 - alpha)% of the scenarios must be feasible.
    params
        Any keyword arguments are passed to the Gurobi model as parameters.
    without_master_scenario
        Do not create a single scenario based on the marginal demand data.
        Such a scenario can strengthen the master problem substantially.
        The single scenario also includes relevant strong inequalities.
    """

    def __init__(
        self,
        data: ProblemData,
        alpha: float,
        without_master_scenario: bool,
        **params,
    ):
        logger.info("Creating master problem.")
        self.model = create_master_model(data, alpha, without_master_scenario)

        for param, value in (DEFAULT_MASTER_PARAMS | params).items():
            logger.debug(f"Setting {param} = {value}.")
            self.model.setParam(param, value)

        dec_vars = self.model.getVars()
        self._y = dec_vars[: data.num_arcs]
        self._z = dec_vars[data.num_arcs : data.num_arcs + data.num_scenarios]

        self.model.update()

    @property
    def c(self) -> np.array:
        return np.array([y.obj for y in self._y])

    def decisions(self) -> np.array:
        return np.array([var.x for var in self._y])

    def decision_names(self) -> list[str]:
        return [var.varName for var in self._y]

    def objective(self) -> float:
        assert self.model.status == GRB.OPTIMAL
        return self.model.objVal

    def add_cut(self, cut: Cut, lazy: bool = True):
        """
        Adds a (possibly lazy) new cut to the model. Gurobi's branch-and-bound
        tree (mostly) respects these new constraints, and uses this to guide
        the search in deeper nodes.
        """
        lhs = LinExpr()
        lhs.addTerms(cut.gamma, self._z[cut.scen])  # type: ignore
        lhs.addTerms(cut.beta, self._y)  # type: ignore

        if lazy:
            self.model.cbLazy(lhs >= cut.gamma)
        else:
            self.model.addConstr(lhs >= cut.gamma)

    def solve_decomposition(
        self,
        subproblems: list[SubProblem],
        with_combinatorial_cut: bool,
    ) -> Result:
        """
        Solves the master/subproblem decomposition with the given subproblems.

        The algorithm uses Gurobi and iteratively adds new constraints/cutting
        planes via a callback whenever Gurobi finds a new feasible, integer
        solution (MIPSOL). We also use the callback to register some runtime
        information, like bounds.

        Parameters
        ----------
        subproblems
            A list of scenario subproblems to solve. The master problem selects
            which subproblems should be made feasible, and adds new constraints
            if they are not yet feasible. These new constraints are derived
            from the (infeasible) subproblems.
        with_combinatorial_cut
            When True, the decomposition also derives a combinatorial cut for
            each infeasible scenario. Such cuts force the first-stage solution
            to chance by opening at least one additional arc if the scenario
            needs to be made feasible.

        Returns
        -------
        Result
            The result object, containing the optimal decisions and additional
            information about the solver process.
        """
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

            y = np.array(model.cbGetSolution(self._y))
            z = np.array(model.cbGetSolution(self._z))

            for z_i, sub in zip(z, subproblems):
                if np.isclose(z_i, 1.0):  # allowed to be infeasible
                    continue

                sub.update_rhs(y)
                sub.solve()

                if sub.is_feasible():  # then there is nothing to do!
                    continue

                # The new constraint "cuts off" the current solution y, so we
                # do not find that one again.
                self.add_cut(sub.feasibility_cut())

                if with_combinatorial_cut:
                    # This cut forces the next solution y to be different from
                    # the current one, unless this scenario is allowed to be
                    # infeasible. This works since the current arc capacity is
                    # infeasible for this scenario, and at least one additional
                    # arc needs to be opened.
                    combinatorial_cut = Cut(np.isclose(y, 0), 1, sub.scenario)
                    self.add_cut(combinatorial_cut)

        self.model.optimize(callback)  # type: ignore

        return Result(
            dict(zip(self.decision_names(), self.decisions())),
            dict(zip(self.decision_names(), self.c)),
            lower_bounds,
            incumbent_objs,
            np.diff(run_times, prepend=0).tolist(),  # type: ignore
        )
