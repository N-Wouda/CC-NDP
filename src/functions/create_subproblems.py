
import numpy as np
from gurobipy import Model
from scipy.sparse import csr_matrix

from src.classes import ProblemData, SubProblem


def create_subproblems(
    data: ProblemData, cls: type[SubProblem]
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


def _create_subproblem(data: ProblemData, cls: type[SubProblem], scen: int):
    orig = data.origins()
    dest = data.destinations()

    num_y_arcs = data.num_arcs  # 1st stage arcs from master problem
    num_x_arcs = num_y_arcs + len(orig) + len(dest)  # 2nd stage variables

    m = Model()
    y = m.addMVar((num_y_arcs,), name="y")  # 1st stage
    x = m.addMVar((num_x_arcs, data.num_commodities), name="x")  # 2nd stage

    # Capacity constraints.
    for idx, arc in enumerate(data.arcs):
        # All flow through an arc must not exceed the arc's capacity.
        m.addConstr(
            x[idx, :].sum() <= arc.capacity * y[idx],
            name=f"capacity{arc.from_node, arc.to_node}",
        )

    # Balance constraints.
    for node in range(1, data.num_nodes + 1):
        arc_idcs_from = data.arc_indices_from(node)
        arc_idcs_to = data.arc_indices_to(node)

        if node in orig:  # at least one commodity originates here
            idcs = [
                idx for idx, c in enumerate(data.commodities) 
                if c.from_node == node
            ]

            # Capacities of artificial arcs to the origin node are non-zero 
            # only for those commodities that originate here.
            rhs = np.zeros(data.num_commodities)
            rhs[idcs] = [data.commodities[idx].demands[scen] for idx in idcs]

            # Add artificial arc from source to the set of incoming arcs at 
            # this node, and constrain the arc's capacities.
            idx = orig.index(node)
            arc_idcs_to.append(num_y_arcs + idx)
            m.addConstr(
                x[num_y_arcs + idx, :] <= rhs,
                name=f"capacity{'u', node}",
            )

        if node in dest:  # at least one commodity needs to go here
            idcs = [
                idx for idx, c in enumerate(data.commodities) 
                if c.to_node == node
            ]

            # Capacities of artificial arcs from the destination node are 
            # non-zero only for those commodities that need to go here.
            rhs = np.zeros(data.num_commodities)
            rhs[idcs] = [data.commodities[idx].demands[scen] for idx in idcs]

            # Add artificial arc to sink to the set of outgoing arcs at this 
            # node, and constrain the arc's capacities.
            idx = dest.index(node)
            arc_idcs_from.append(num_y_arcs + len(orig) + idx)
            m.addConstr(
                x[num_y_arcs + len(orig) + idx, :] <= rhs,
                name=f"capacity{node, 'v'}",
            )

        for commodity_idx in range(data.num_commodities):
            lhs = x[arc_idcs_from, commodity_idx].sum()
            rhs = x[arc_idcs_to, commodity_idx].sum()
            m.addConstr(lhs == rhs, name=f"balance{node, commodity_idx}")

    # Demand constraint at the "artificial sink" v. This covers all demand
    # across all commodities in the scenario.
    demand = sum(c.demands[scen] for c in data.commodities)
    m.addConstr(x[-len(dest):, :].sum() >= demand, name="demand(v)")

    m.update()

    mat = m.getA()
    constrs = m.getConstrs()
    dec_vars = m.getVars()

    T = csr_matrix(mat[:, : data.num_arcs])
    W = csr_matrix(mat[:, data.num_arcs :])
    h = [constr.rhs for constr in constrs]
    senses = [constr.sense for constr in constrs]
    vname = [var.varName for var in dec_vars[data.num_arcs :]]
    cname = [constr.constrName for constr in constrs]

    return cls(T, W, h, senses, vname, cname, scen)
