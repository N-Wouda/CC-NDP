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
        x = dec_vars[: -len(subs)]
        z = dec_vars[-len(subs) :]

        for idx, sub in enumerate(subs):
            self._add_subproblem(x, z[idx], sub)

    def solve(self, time_limit: float = np.inf) -> Optional[Result]:
        logger.info(f"Solving DEQ with time_limit={time_limit:.2f}s.")

        self.model.setParam("TimeLimit", time_limit)
        self.model.optimize()

        if self.model.SolCount == 0:
            logger.error("Solver found no solution.")
            return None

        if self.model.status == GRB.TIME_LIMIT:
            logger.warning("Solver ran out of time - solution is not optimal.")
            logger.info(f"Gap: {100 * self.model.MIPGap:.2f}%")

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

    def _add_subproblem(self, x: MVar, z: Var, sub: SubProblem):
        n_vars = sub.W.shape[1]
        dec_vars = sub.model.getVars()[:n_vars]

        obj = [var.obj for var in dec_vars]
        lb = [var.lb for var in dec_vars]
        ub = [var.ub for var in dec_vars]
        vtype = [var.vtype for var in dec_vars]

        f = self.model.addMVar(
            (len(dec_vars),),
            lb,  # type: ignore
            ub,  # type: ignore
            obj,  # type: ignore
            vtype,  # type: ignore
            name=f"f_{sub.scenario}",
        )

        # The last constraint is the demand constraint, sum(f) >= d(omega). We
        # here impose that sum(f) + 1.01 d(omega) z_i >= d(omega), that is, we
        # always satisfy the demand constraint when the scenario is allowed to
        # be infeasible.
        m = np.zeros_like(sub.h)
        m[-1] = 1.01 * sub.h[-1]  # times 1.01 to avoid numerical issues

        self.model.addMConstr(
            hstack([sub.T, sub.W, m]),
            x + f.tolist() + [z],
            sense=sub.senses,
            b=sub.h,
        )
