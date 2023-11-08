from collections import defaultdict

import numpy as np
from gurobipy import Model
from scipy.sparse import csr_matrix

from src.classes import ProblemData, SubProblem


def create_subproblems(data: ProblemData, cls: type[SubProblem]) -> list[SubProblem]:
    """
    Creates the subproblems.

    Parameters
    ----------
    data
        Problem data instance.
    cls
        Type of subproblem formulation to use.

    Returns
    -------
    list
        List of created subproblems. These are instance of the ``cls`` passed
        into this function.
    """
    return [_create_subproblem(data, cls, scen) for scen in range(data.num_scenarios)]


def _create_subproblem(data: ProblemData, cls: type[SubProblem], scen: int):
    num_y_edges = data.num_edges  # constructed by master problem
    num_x_edges = num_y_edges + ... # second-stage flow variables

    m = Model()

    y = m.addMVar((num_y_edges,), name="y")  # first-stage vars
    x = m.addMVar((num_x_edges,), name="x")  # second-stage vars

    # Capacity constraints
    # TODO

    # Balance constraints
    # TODO

    # Demand constraint at the "artificial sink" t.
    # TODO

    m.update()

    mat = m.getA()
    constrs = m.getConstrs()
    dec_vars = m.getVars()

    T = csr_matrix(mat[:, : data.num_edges])
    W = csr_matrix(mat[:, data.num_edges :])
    h = [constr.rhs for constr in constrs]
    senses = [constr.sense for constr in constrs]
    vname = [var.varName for var in dec_vars[data.num_edges :]]
    cname = [constr.constrName for constr in constrs]

    return cls(T, W, h, senses, vname, cname, scen)
