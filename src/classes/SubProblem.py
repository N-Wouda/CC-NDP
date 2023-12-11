from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

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
    """

    def __init__(self, data: ProblemData, scen: int, **params):
        logger.info(f"Creating {self.__class__.__name__} #{scen}.")

        self.scenario = scen

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

    def cut(self) -> Cut:
        duals = self.duals()
        beta = duals.transpose() @ self.T
        gamma = float(duals @ self.h)

        return Cut(beta, gamma, self.scenario)

    def duals(self) -> np.ndarray:
        return np.array([constr.pi for constr in self._constrs])

    def is_feasible(self) -> bool:
        return np.isclose(self.objective(), 0.0)  # type: ignore

    def objective(self) -> float:
        assert self.model.status == GRB.OPTIMAL
        return self.model.objVal

    def solve(self):
        self.model.optimize()

    def update_rhs(self, y: np.ndarray):
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
            name=f"capacity{arc.from_node, arc.to_node}",
        )

    for node in range(1, data.num_nodes + 1):
        arc_idcs_from = data.arc_indices_from(node)
        arc_idcs_to = data.arc_indices_to(node)

        for commodity_idx, commodity in enumerate(data.commodities):
            # Demand constraint.
            if node == commodity.to_node:  # is the commodity destination
                name = f"demand{node, commodity_idx}"
                to = x[arc_idcs_to, commodity_idx].sum()
                m.addConstr(to >= demands[commodity_idx], name=name)

            # Balance constraint.
            elif node != commodity.from_node:  # regular intermediate node
                frm = x[arc_idcs_from, commodity_idx].sum()
                to = x[arc_idcs_to, commodity_idx].sum()
                m.addConstr(to == frm, name=f"balance{node, commodity_idx}")

    m.update()
    return m
