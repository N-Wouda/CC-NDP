from collections import defaultdict
from typing import Type

import numpy as np
from gurobipy import Model
from scipy.sparse import csr_matrix

from ccndp.classes import FacilityNode as Facility
from ccndp.classes import ProblemData
from ccndp.classes import SinkNode as Sink
from ccndp.classes import SourceNode as Source
from ccndp.classes import SubProblem


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
    return [
        _create_subproblem(data, cls, scen)
        for scen in range(data.num_scenarios)
    ]


def _create_subproblem(data: ProblemData, cls: Type[SubProblem], scen: int):
    # Constructed by master problem
    num_x_edges = data.num_edges

    # Constructed + artificial in subproblem
    sources = data.sources()
    sinks = data.sinks()
    num_f_edges = num_x_edges + len(sources) + len(sinks)

    m = Model()

    x = m.addMVar((num_x_edges,), name="x")  # first-stage vars
    f = m.addMVar((num_f_edges,), name="f")  # second-stage vars

    # Subsets of the flow variables related to the artificial edges and nodes
    # inserted into the network flow graph. f_source are all flows from the
    # artificial source s to the sources in the actual graph, f_sink all flows
    # from sinks in the actual graph to the artificial sink t, and f_t the
    # collected flow at t.
    f_source = f[num_x_edges : num_x_edges + len(sources)]
    f_sink = f[-len(sinks) :]

    # Capacity constraints for "x decisions" from the first stage.
    for x_i, f_i, edge in zip(x, f, data.edges):
        m.addConstr(f_i <= edge.capacity[scen] * x_i, name=f"capacity({edge})")

    # Capacity constraints (from each sink node to the "artificial sink" t).
    demand = np.array([sink.demand[scen] for sink in sinks])
    for idx, f_i, d in zip(range(len(sinks)), f_sink, demand):
        m.addConstr(f_i <= d, name=f"capacity(sink{idx}, t)")

    # Balance constraints
    for node in data.nodes:
        idcs_in = data.edge_indices_to(node)
        idcs_out = data.edge_indices_from(node)

        f_in = f[idcs_in]
        f_out = f[idcs_out]

        if isinstance(node, Sink):
            # For sinks there's only the balance constraint at the sink node,
            # there's no additional construction at the node itself.
            idx = node.idx - min(sink.idx for sink in sinks)
            m.addConstr(f_sink[idx] == sum(f_in), name=f"balance({node})")
            continue

        if isinstance(node, Source):
            # The inflow is the arc from the "artificial source" s.
            f_in = [f_source[node.idx]]

        # Balance constraints. The graph around this node looks like:
        #   nodes --(f_in)--> [edge_node] --(f_out)-> nodes
        edge_node = f[data.edge_index_of((node, node))]

        if isinstance(node, Facility):
            # Facilities can only produce the minimum of all input resource
            # flows. This reduces to a regular flow balance constraint in case
            # there is only a single resource.
            edges_in = [data.edges[idx] for idx in idcs_in]
            by_res = defaultdict(list)

            for edge, flow in zip(edges_in, f_in):
                assert isinstance(edge.frm, (Source, Facility))
                by_res[edge.frm.makes].append(flow)

            for res, flows in by_res.items():
                m.addConstr(
                    edge_node == sum(flows),  # TODO eta
                    name=f"balance({node}, in, {res})",
                )
        else:
            # Regular in == out balance constraint for all non-facility nodes.
            m.addConstr(edge_node == sum(f_in), name=f"balance({node}, in)")

        m.addConstr(sum(f_out) == edge_node, name=f"balance({node}, out)")

    # Demand constraint at the "artificial sink" t.
    m.addConstr(f_sink.sum() >= demand.sum(), name="demand(t)")

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
