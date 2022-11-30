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
    # TODO make this work with in/out edges?
    m = Model()

    # x = m.addMVar((data.num_edges,), name="x")  # first-stage vars
    # f = m.addMVar((data.num_edges,), name="f")  # second-stage vars
    #
    # # Demand constraints
    # for sink, demand in zip(data.sinks(), data.demands[scen]):
    #     incoming = data.edge_idcs_to_node(sink)
    #     m.addConstr(f[incoming].sum() >= demand, name=f"demand[{sink}]")
    #
    # # Capacity constraints
    # for x_i, f_i, c, (i, j) in zip(x, f, data.capacities[scen], data.edges):
    #     m.addConstr(f_i <= c * x_i, name=f"capacity[{i}, {j}]")
    #
    # # Balance constraints
    # for idx, node in enumerate(data.nodes):
    #     if node.is_sink:
    #         continue
    #
    #     # TODO eta? node type?
    #     edge_node = f[data.get_node_edge_index(node)]
    #
    #     if indices_in := data.edge_idcs_to_node(node):
    #         incoming = f[indices_in].sum()
    #         m.addConstr(edge_node <= incoming, name=f"balance[{node}, in]")
    #
    #     if indices_out := data.edge_idcs_from_node(node):
    #         outgoing = f[indices_out].sum()
    #         m.addConstr(outgoing <= edge_node, name=f"balance[{node}, out]")

    m.update()

    mat = m.getA()
    constrs = m.getConstrs()
    dec_vars = m.getVars()

    T = csr_matrix(mat[:, : data.num_edges])
    W = csr_matrix(mat[:, data.num_edges :])
    h = [constr.rhs for constr in constrs]
    senses = [constr.sense for constr in constrs]
    vname = [var.VarName for var in dec_vars[data.num_edges :]]
    cname = [constr.constrName for constr in constrs]

    return cls(T, W, h, senses, vname, cname, scen)
