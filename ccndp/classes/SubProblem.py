from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import numpy as np
from gurobipy import GRB, Constr, Model, Var
from scipy.sparse import csr_matrix

from ccndp.config import DEFAULT_SUB_PARAMS

from .Cut import Cut

logger = logging.getLogger(__name__)


class SubProblem(ABC):
    """
    Abstract base class for a subproblem formulation.
    """

    def __init__(
        self,
        T: csr_matrix,
        W: csr_matrix,
        h: list[float] | np.array,
        senses: list[str] | np.array,
        vname: list[str],
        cname: list[str],
        scen: int,
        **params,
    ):
        logger.info(f"Creating {self.__class__.__name__} #{scen}.")

        self.scenario = scen

        self.T = T
        self.W = W
        self.h = np.array(h).reshape((len(h), 1))
        self.senses = np.array(senses)
        self.vname = vname
        self.cname = cname

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

    def update_rhs(self, x: np.ndarray):
        rhs = self.h - self.T @ x[..., np.newaxis]
        rhs[rhs < 0] = 0  # is only ever negative due to rounding errors

        self.model.setAttr("RHS", self._constrs, rhs)  # type: ignore
