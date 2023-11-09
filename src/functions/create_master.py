import numpy as np
from gurobipy import MVar, Model

from src.classes import MasterProblem, ProblemData


def create_master(
    data: ProblemData, alpha: float, no_vis: bool
) -> MasterProblem:
    """
    Creates the master problem.

    Parameters
    ----------
    data
        Problem data instance.
    alpha
        Controls the percentage of scenarios that can be infeasible: at least
        (1 - alpha)% of the scenarios must be feasible.
    no_vis
        Whether to include the valid inequalities (VI's) in the model. These
        are not strictly needed, but help the formulation solve much faster.
        If True, VI's are not added; else they are.

    Returns
    -------
    MasterProblem
        The created master problem instance.
    """
    m = Model()

    # Construction decision variables, with costs and variable types as given
    # by the problem instance.
    y = m.addMVar(
        (data.num_arcs,),
        obj=[arc.fixed_cost for arc in data.arcs],  # type: ignore
        vtype="B",  # type: ignore
        name="y",
    )

    # The z variables decide which of the scenarios must be made feasible. If
    # z_i == 1, scenario i can be infeasible; if z_i == 0, it must be feasible.
    z = m.addMVar((data.num_scenarios,), vtype="B", name="z")

    # At most alpha percent of the scenarios can be infeasible.
    m.addConstr(z.sum() <= alpha * data.num_scenarios, name="scenarios")

    if not no_vis:
        _add_vis(data, alpha, m, y, z)

    m.update()

    A = m.getA()
    constrs = m.getConstrs()
    dec_vars = m.getVars()

    obj = [var.obj for var in dec_vars]
    lb = [var.lb for var in dec_vars]
    ub = [var.ub for var in dec_vars]
    vtype = [var.vtype for var in dec_vars]
    vname = [var.varName for var in dec_vars]
    cname = [constr.constrName for constr in constrs]
    b = [constr.rhs for constr in constrs]
    senses = [constr.sense for constr in constrs]

    return MasterProblem(
        obj, A, b, senses, vtype, lb, ub, vname, cname, data.num_scenarios
    )


def _add_vis(data: ProblemData, alpha: float, m: Model, y: MVar, z: MVar):
    """
    Adds (static) valid inequalities to the given model.
    """
    for scen in range(data.num_scenarios):
        demand = sum(c.demands[scen] for c in data.commodities)

        from_orig = [
            idx
            for node in data.origins()
            for idx in data.arc_indices_from(node)
        ]
        orig_cap = np.array([data.arcs[idx].capacity for idx in from_orig])
        m.addConstr(orig_cap @ y[from_orig] >= demand * (1 - z[scen]))

        to_dest = [
            idx
            for node in data.destinations()
            for idx in data.arc_indices_to(node)
        ]
        dest_cap = np.array([data.arcs[idx].capacity for idx in to_dest])
        m.addConstr(dest_cap @ y[to_dest] >= demand * (1 - z[scen]))

        for node in data.origins():
            commodities = [c for c in data.commodities if c.from_node == node]
            demand = sum(c.demands[scen] for c in commodities)

            from_node = data.arc_indices_from(node)
            orig_cap = np.array([data.arcs[idx].capacity for idx in from_node])
            m.addConstr(orig_cap @ y[from_node] >= demand * (1 - z[scen]))

        for node in data.destinations():
            commodities = [c for c in data.commodities if c.to_node == node]
            demand = sum(c.demands[scen] for c in commodities)

            to_node = data.arc_indices_to(node)
            dest_cap = np.array([data.arcs[idx].capacity for idx in to_node])
            m.addConstr(dest_cap @ y[to_node] >= demand * (1 - z[scen]))
