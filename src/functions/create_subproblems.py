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
    num_y_arcs = data.num_arcs  # 1st stage arcs from master problem
    num_x_arcs = num_y_arcs  # 2nd stage variables

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

        for commodity_idx, commodity in enumerate(data.commodities):
            frm = x[arc_idcs_from, commodity_idx].sum()
            to = x[arc_idcs_to, commodity_idx].sum()

            if node == commodity.to_node:  # is the commodity destination
                name = f"demand{node, commodity_idx}"
                m.addConstr(to - frm >= commodity.demands[scen], name=name)
            elif node != commodity.from_node:  # regular intermediate node
                m.addConstr(to == frm, name=f"balance{node, commodity_idx}")

    m.update()

    mat = m.getA()
    constrs = m.getConstrs()
    dec_vars = m.getVars()

    T = csr_matrix(mat[:, :num_y_arcs])
    W = csr_matrix(mat[:, num_y_arcs:])
    h = [constr.rhs for constr in constrs]
    senses = [constr.sense for constr in constrs]
    vname = [var.varName for var in dec_vars[num_y_arcs:]]
    cname = [constr.constrName for constr in constrs]

    return cls(T, W, h, senses, vname, cname, scen)
