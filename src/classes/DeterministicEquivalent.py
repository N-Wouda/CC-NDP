import logging
from typing import List, Optional

import numpy as np
from gurobipy import GRB, MVar, Var
from scipy.sparse import hstack

from .MasterProblem import MasterProblem
from .Result import Result
from .SubProblem import SubProblem

logger = logging.getLogger(__name__)


class DeterministicEquivalent:
    """
    Generates and solves a deterministic equivalent (DEQ) formulation of the
    given master and subproblems.
    """

    def __init__(self, master: MasterProblem, subs: List[SubProblem]):
        logger.info("Creating deterministic equivalent (DEQ).")

        self.master = master
        self.subs = subs
        self.model = master.model.copy()

        dec_vars = self.model.getVars()
        num_arcs = len(master.c)
        num_scen = len(subs)
        y = dec_vars[:num_arcs]
        z = dec_vars[num_arcs : num_arcs + num_scen]

        for idx, sub in enumerate(subs):
            self._add_subproblem(y, z[idx], sub)

    def solve(self, time_limit: float = np.inf) -> Optional[Result]:
        logger.info(f"Solving DEQ with {time_limit = :.2f} seconds.")

        self.model.setParam("TimeLimit", time_limit)
        self.model.optimize()

        if self.model.SolCount == 0:
            logger.error("Solver found no solution.")
            return None

        if self.model.status == GRB.TIME_LIMIT:
            logger.warning("Solver ran out of time - solution is not optimal.")
            logger.info(f"Gap: {100 * self.model.MIPGap:.2f}%.")

        logger.info(f"Solving took {self.model.runTime:.2f}s.")

        dec_vars = self.model.getVars()
        x = dec_vars[: -len(self.subs)]

        return Result(
            dict(zip(self.master.decision_names(), (var.x for var in x))),
            dict(zip(self.master.decision_names(), self.master.c)),
            [self.model.objBound],
            [self.model.objVal],
            [self.model.runTime],
            self.model.status == GRB.OPTIMAL,
        )

    def _add_subproblem(self, y: MVar, z: Var, sub: SubProblem):
        dec_vars = sub.model.getVars()[: sub.W.shape[1]]
        x = self.model.addMVar(
            (len(dec_vars),),
            [var.lb for var in dec_vars],  # type: ignore
            [var.ub for var in dec_vars],  # type: ignore
            [var.obj for var in dec_vars],  # type: ignore
            [var.vtype for var in dec_vars],  # type: ignore
            name=f"x_{sub.scenario}",
        )

        # The right-hand side vector (h) consists of zeros and non-zero demand
        # terms. On the left hand side we add a column depending on h that
        # automatically makes the scenario feasible if z is one. To avoid
        # numerical issues, we multiply h by 1.01.
        self.model.addMConstr(
            hstack([sub.T, sub.W, 1.01 * sub.h]),
            y + x.tolist() + [z],
            sense=sub.senses,
            b=sub.h,
        )
