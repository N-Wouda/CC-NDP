from typing import Type

from gurobipy import Model
from scipy.sparse import csr_matrix

from src.classes import ProblemData, SubProblem


def create_subproblems(
    data: ProblemData, cls: Type[SubProblem]
) -> list[SubProblem]:
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
    # TODO only call Gurobi once; it is fairly slow. Instead update matrices
    #  directly.
    return [
        _create_subproblem(data, cls, scen)
        for scen in range(data.num_scenarios)
    ]


def _create_subproblem(data: ProblemData, cls: Type[SubProblem], scen: int):
    m = Model()

    x = m.addMVar((data.num_edges,), name="x")  # first-stage vars
    f = m.addMVar((data.num_edges,), name="f")  # second-stage vars

    # Demand constraints
    for sink, demand in zip(data.sink_nodes, data.demand[scen]):
        incoming = data.edge_idcs_to_node(sink)
        m.addConstr(f[incoming].sum() >= demand, f"demand[{sink}]")

    # Capacity constraints
    for x_i, f_i, c, (i, j) in zip(x, f, data.capacity[scen], data.edges):
        m.addConstr(f_i <= c * x_i, f"capacity[{i}, {j}]")

    # Balance constraints
    for idx, node in enumerate(data.nodes):
        incoming = data.edge_idcs_to_node(node)
        outgoing = data.edge_idcs_from_node(node)

        if incoming and outgoing:
            # TODO eta? node type?
            lhs = f[outgoing].sum()
            rhs = f[incoming].sum()
            m.addConstr(lhs <= rhs, f"balance[{node}]")

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
