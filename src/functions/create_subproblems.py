from typing import Type

import numpy as np
from gurobipy import Model
from scipy.sparse import csr_matrix

from src.classes import ProblemData, SinkNode, SourceNode, SubProblem


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
    # Constructed by master problem
    num_x_edges = data.num_edges

    # Constructed + artificial in subproblem
    sinks = data.sinks()
    num_f_edges = num_x_edges + len(data.sources()) + len(sinks)

    m = Model()

    x = m.addMVar((num_x_edges,), name="x")  # first-stage vars
    f = m.addMVar((num_f_edges,), name="f")  # second-stage vars

    # Capacity constraints (only for "x decisions" from the first stage)
    for x_i, f_i, edge in zip(x, f, data.edges):
        m.addConstr(f_i <= edge.capacity[scen] * x_i, name=f"capacity{edge}")

    # Balance constraints
    for node in data.nodes:
        # TODO eta? node type?
        f_in = f[data.edge_indices_to(node)]
        f_out = f[data.edge_indices_from(node)]

        if isinstance(node, SinkNode):
            # For sinks there's only the balance constraint at the sink node,
            # there's no additional construction at the node itself.
            f_out = [f[-node.idx - 1]]
            m.addConstr(sum(f_out) <= sum(f_in), name=f"balance({node})")
            continue

        if isinstance(node, SourceNode):
            # The inflow is the arc from the "artificial source" s.
            f_in = [f[-len(sinks) - node.idx - 1]]

        # This edge is flow through the node itself.
        edge_node = f[data.edge_index_of((node, node))]

        # Two constraints, one for the flow into the node, and one for the
        # flow out of it.
        m.addConstr(edge_node <= sum(f_in), name=f"balance({node}, in)")
        m.addConstr(sum(f_out) <= edge_node, name=f"balance({node}, out)")

    # Demand constraints (from each sink node to the "artificial sink" t)
    demand = np.array([sink.demand[scen] for sink in sinks])
    for idx, f_i, d in zip(range(len(sinks)), f[-len(sinks) :], demand):
        m.addConstr(f_i >= d, name=f"demand(sink{idx}, t)")

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
