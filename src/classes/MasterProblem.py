from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from gurobipy import GRB, LinExpr, MVar, Model

from src.config import DEFAULT_MASTER_PARAMS

from .Result import Result
from .RootResult import RootResult

if TYPE_CHECKING:
    from .Cut import Cut
    from .ProblemData import ProblemData
    from .SubProblem import SubProblem

logger = logging.getLogger(__name__)


class MasterProblem:
    """
    Master problem formulation. The model looks something like:

        min  c y
        s.t.      Ay ~ b
             sum(z) <= alpha N
             y mixed-integer, z binary

    The variables y in this model are passed to the scenario subproblems.

    Parameters
    ----------
    data
        Problem data instance.
    alpha
        Controls the percentage of scenarios that can be infeasible: at least
        (1 - alpha)% of the scenarios must be feasible.
    no_vis
        Whether to include the valid inequalities (VI's) in the model. These
        are not strictly needed, but help the formulation solve much faster.
        If True, VI's are not added; else they are.
    params
        Any keyword arguments are passed to the Gurobi model as parameters.
    """

    def __init__(
        self, data: ProblemData, alpha: float, no_vis: bool, **params
    ):
        logger.info("Creating master problem.")

        self.model = _create_model(data, alpha, no_vis)

        for param, value in (DEFAULT_MASTER_PARAMS | params).items():
            logger.debug(f"Setting {param} = {value}.")
            self.model.setParam(param, value)

        dec_vars = self.model.getVars()
        self._y = dec_vars[: -data.num_scenarios]
        self._z = dec_vars[-data.num_scenarios :]

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

    def compute_root_relaxation(self) -> RootResult:
        """
        Computes the root relaxations, that is, the value of the LP or MIP
        solution at the root node.
        """
        logger.info("Computing LP root relaxation.")

        self.model.reset()
        relax = self.model.relax()
        relax.optimize()

        assert relax.status == GRB.OPTIMAL

        logger.info("Computing MIP root relaxation.")

        self.model.reset()
        self.model.optimize()

        assert self.model.status == GRB.OPTIMAL

        return RootResult(
            relax.runTime,
            relax.objVal,
            self.model.runTime,
            self.model.objVal,
        )

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
            z = np.array(model.cbGetSolution(self._z), dtype=int)

            for z_i, sub in zip(z, subproblems):
                if z_i == 1:  # scenario is not selected, so is allowed to be
                    continue  # infeasible in this iteration.

                sub.update_rhs(y)
                sub.solve()

                if not sub.is_feasible():
                    # The new constraint "cuts off" the current solution y,
                    # ensuring we do not find that one again.
                    self.add_cut(sub.cut())

                    if with_combinatorial_cut:
                        # This cut forces the next solution y to be different
                        # from the current one, unless this scenario is allowed
                        # to be infeasible. This works since the current arc
                        # capacity is infeasible for this scenario, and at
                        # least one additional arc needs to be opened.
                        lhs = np.isclose(y, 0) @ self._y
                        rhs = 1 - self._z[sub.scenario]
                        model.cbLazy(lhs >= rhs)

        self.model.optimize(callback)  # type: ignore

        return Result(
            dict(zip(self.decision_names(), self.decisions())),
            dict(zip(self.decision_names(), self.c)),
            lower_bounds,
            incumbent_objs,
            np.diff(run_times, prepend=0).tolist(),  # type: ignore
        )


def _create_model(data: ProblemData, alpha: float, no_vis: bool) -> Model:
    m = Model()

    # Construction decision variables, with costs and variable types as given
    # by the problem instance.
    y = m.addMVar(
        (data.num_arcs,),
        obj=[arc.fixed_cost for arc in data.arcs],  # type: ignore
        vtype="B",  # type: ignore
        name=[str(arc) for arc in data.arcs],
    )

    # The z variables decide which of the scenarios must be made feasible. If
    # z_i == 1, scenario i can be infeasible; if z_i == 0, it must be feasible.
    z = m.addMVar((data.num_scenarios,), vtype="B", name="z")

    # At most alpha percent of the scenarios can be infeasible.
    m.addConstr(z.sum() <= alpha * data.num_scenarios, name="scenarios")

    if not no_vis:
        _add_vis(data, alpha, m, y, z)

    m.update()
    return m


def _add_vis(data: ProblemData, alpha: float, m: Model, y: MVar, z: MVar):
    for scen in range(data.num_scenarios):
        demand = sum(c.demands[scen] for c in data.commodities)

        from_orig = [
            idx
            for node in data.origins()
            for idx in data.arc_indices_from(node)
        ]
        orig_cap = np.array([data.arcs[idx].capacity for idx in from_orig])
        m.addConstr(orig_cap @ y[from_orig] >= demand * (1 - z[scen]))

        to_dest = [
            idx
            for node in data.destinations()
            for idx in data.arc_indices_to(node)
        ]
        dest_cap = np.array([data.arcs[idx].capacity for idx in to_dest])
        m.addConstr(dest_cap @ y[to_dest] >= demand * (1 - z[scen]))

        for node in data.origins():
            commodities = [c for c in data.commodities if c.from_node == node]
            demand = sum(c.demands[scen] for c in commodities)

            from_node = data.arc_indices_from(node)
            orig_cap = np.array([data.arcs[idx].capacity for idx in from_node])
            m.addConstr(orig_cap @ y[from_node] >= demand * (1 - z[scen]))

        for node in data.destinations():
            commodities = [c for c in data.commodities if c.to_node == node]
            demand = sum(c.demands[scen] for c in commodities)

            to_node = data.arc_indices_to(node)
            dest_cap = np.array([data.arcs[idx].capacity for idx in to_node])
            m.addConstr(dest_cap @ y[to_node] >= demand * (1 - z[scen]))
