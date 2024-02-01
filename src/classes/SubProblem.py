from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import igraph as ig
import numpy as np
from gurobipy import GRB, Constr, Model, Var
from scipy.sparse import csr_matrix

from src.config import DEFAULT_SUB_PARAMS
from src.functions import create_sub_model

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

        demands = np.array([c.demands[scen] for c in data.commodities])
        model = create_sub_model(data, demands)

        mat = model.getA()
        constrs = model.getConstrs()
        dec_vars = model.getVars()

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
