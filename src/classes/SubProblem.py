from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator

import igraph as ig
import numpy as np
from gurobipy import GRB, Constr, Model, Var
from scipy.sparse import csr_matrix

from src.config import DEFAULT_SUB_PARAMS

from .Cut import Cut

if TYPE_CHECKING:
    from .ProblemData import ProblemData

logger = logging.getLogger(__name__)


class SubProblem(ABC):
    """
    Abstract base class for a subproblem formulation.

    Parameters
    ----------
    data
        Problem data instance.
    scen
        Scenario or subproblem number.
    without_metric_cuts
        Do not derive stronger metric feasibility cuts? These strengthen the
        constant in the feasibility cuts.
    """

    def __init__(
        self,
        data: ProblemData,
        scen: int,
        without_metric_cuts: bool,
        **params,
    ):
        logger.info(f"Creating {self.__class__.__name__} #{scen}.")

        self.scenario = scen
        self.without_metric_cuts = without_metric_cuts

        m = _create_model(data, scen)
        mat = m.getA()
        constrs = m.getConstrs()
        dec_vars = m.getVars()

        self.T = csr_matrix(mat[:, : data.num_arcs])
        self.W = csr_matrix(mat[:, data.num_arcs :])
        self.senses = [constr.sense for constr in constrs]
        self.vname = [var.varName for var in dec_vars[data.num_arcs :]]
        self.cname = [constr.constrName for constr in constrs]

        h = [constr.rhs for constr in constrs]
        self.h = np.array(h).reshape((len(h), 1))

        self.model = Model(f"Sub #{self.scenario}")

        self.data = data
        self._y = np.zeros(data.num_arcs)
        self.graph = ig.Graph(
            n=data.num_nodes + 1,
            edges=[(a.from_node, a.to_node) for a in data.arcs],
            directed=True,
        )

        for param, value in (DEFAULT_SUB_PARAMS | params).items():
            logger.debug(f"Setting {param} = {value}.")
            self.model.setParam(param, value)

        self._vars = self._set_vars()
        self._constrs = self._set_constrs()

        for var, name in zip(self._vars, self.vname):
            var.varName = name

        for constr, name in zip(self._constrs, self.cname):
            constr.constrName = name

        self.model.update()

    @abstractmethod
    def _set_vars(self) -> list[Var]:
        return NotImplemented

    @abstractmethod
    def _set_constrs(self) -> list[Constr]:
        return NotImplemented

    def cutset_inequalities(self) -> Generator[Cut, None, None]:
        # TODO think about these
        # TODO fix this to make it work with the removed flows (see model
        #   creation)
        # TODO aggregate by origin/destination?
        n_arcs = self.data.num_arcs
        n_comm = self.data.num_commodities

        # Current flow values.
        x = np.array(self.model.getAttr("X", self._vars[: n_arcs * n_comm]))
        flows = x.reshape(n_arcs, n_comm)

        # Capacity of each arc (as if it were constructed).
        arc_capacity = np.array([a.capacity for a in self.data.arcs])

        # Residual capacity of the current solution y and flow values x.
        arc_residual = (arc_capacity * self._y - flows.sum(axis=1)).tolist()

        for commodity_idx, commodity in enumerate(self.data.commodities):
            demand = commodity.demands[self.scenario]

            # First check if this commodity is not already feasible. We can
            # skip this commodity if that's the case.
            arcs_out = self.data.arc_indices_from(commodity.from_node)
            if flows[arcs_out, commodity_idx].sum() >= demand:
                continue

            # The current solution does not have sufficient flow of this
            # commodity out of the origin node. That means the residual graph
            # has a bottleneck somewhere. We find a minimum cut in the residual
            # graph and yield a cut that forces the capacity of the edges on
            # that cut to be at least the commodity's demand in this scenario.
            cut = self.graph.mincut(
                commodity.from_node,
                commodity.to_node,
                arc_residual,
            )

            beta = np.zeros_like(arc_capacity)
            beta[cut.cut] = arc_capacity[cut.cut]

            yield Cut(beta, demand, self.scenario)

    def feasibility_cut(self) -> Cut:
        duals = np.array(self.model.getAttr("Pi", self._constrs))
        beta = duals.transpose() @ self.T

        if self.without_metric_cuts:  # then return basic feasibility cut
            gamma = float(duals @ self.h)
            return Cut(beta, gamma, self.scenario)

        # Derive a stronger constant (gamma) for use in cuts. This is a metric
        # inequality. See the paper by Costa et al. (2009) for details:
        # https://doi.org/10.1007/s10589-007-9122-0.
        pi = -duals[: self.data.num_arcs]
        pi[pi < 0] = 0  # is only ever negative due to rounding errors

        gamma = 0
        for commodity in self.data.commodities:
            edge_idcs = self.graph.get_shortest_path(
                commodity.from_node,
                commodity.to_node,
                weights=pi,
                output="epath",
            )

            gamma += commodity.demands[self.scenario] * pi[edge_idcs].sum()

        return Cut(beta, gamma, self.scenario)

    def is_feasible(self) -> bool:
        return np.isclose(self.objective(), 0.0)  # type: ignore

    def objective(self) -> float:
        assert self.model.status == GRB.OPTIMAL
        return self.model.objVal

    def solve(self):
        self.model.optimize()

    def update_rhs(self, y: np.ndarray):
        self._y = y

        rhs = self.h - self.T @ y[..., np.newaxis]
        rhs[rhs < 0] = 0  # is only ever negative due to rounding errors

        self.model.setAttr("RHS", self._constrs, rhs)  # type: ignore


def _create_model(data: ProblemData, scen: int) -> Model:
    demands = np.array([c.demands[scen] for c in data.commodities])

    m = Model()
    y = m.addMVar((data.num_arcs,), name="y")  # 1st stage
    x = m.addMVar((data.num_arcs, data.num_commodities), name="x")  # 2nd stage

    # Capacity constraints.
    for idx, arc in enumerate(data.arcs):
        # All flow through an arc must not exceed the arc's capacity.
        m.addConstr(
            x[idx, :].sum() <= arc.capacity * y[idx],
            name=f"capacity{arc}",
        )

    # Balance constraints.
    for commodity_idx, commodity in enumerate(data.commodities):
        for node in range(1, data.num_nodes + 1):
            frm = x[data.arc_indices_from(node), commodity_idx].sum()
            to = x[data.arc_indices_to(node), commodity_idx].sum()

            if node == commodity.to_node:  # is the commodity destination
                name = f"demand{node, commodity_idx}"
                m.addConstr(to >= demands[commodity_idx], name=name)
            elif node == commodity.from_node:  # is the commodity origin
                name = f"supply{node, commodity_idx}"
                m.addConstr(frm >= demands[commodity_idx], name=name)
            else:  # is a regular intermediate node
                name = f"balance{node, commodity_idx}"
                m.addConstr(to == frm, name=name)

        # Remove superfluous flows: those out of the destination, or into the
        # origin. These must be set to zero, and can thus be removed from the
        # model.
        m.remove(x[data.arc_indices_to(commodity.from_node), commodity_idx])
        m.remove(x[data.arc_indices_from(commodity.to_node), commodity_idx])

    m.update()
    return m
