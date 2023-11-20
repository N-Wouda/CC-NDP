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
    demands = np.array([c.demands[scen] for c in data.commodities])
    m = _create_model(data, demands)

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


def _create_model(data: ProblemData, demands: np.array) -> Model:
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

    # Balance constraints.
    for node in range(1, data.num_nodes + 1):
        arc_idcs_from = data.arc_indices_from(node)
        arc_idcs_to = data.arc_indices_to(node)

        for commodity_idx, commodity in enumerate(data.commodities):
            if node == commodity.to_node:  # is the commodity destination
                name = f"demand{node, commodity_idx}"
                to = x[arc_idcs_to, commodity_idx].sum()
                m.addConstr(to >= demands[commodity_idx], name=name)
            elif node != commodity.from_node:  # regular intermediate node
                frm = x[arc_idcs_from, commodity_idx].sum()
                to = x[arc_idcs_to, commodity_idx].sum()
                m.addConstr(to == frm, name=f"balance{node, commodity_idx}")

    return m
