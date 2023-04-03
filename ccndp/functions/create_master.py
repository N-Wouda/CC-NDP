import itertools

import numpy as np
from gurobipy import MVar, Model

from ccndp.classes import MasterProblem, ProblemData


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
    x = m.addMVar(
        (data.num_edges,),
        obj=data.costs(),  # type: ignore
        vtype=data.vtypes(),  # type: ignore
        name=[str(edge) for edge in data.edges],  # type: ignore
    )

    # The z variables decide which of the scenarios must be made feasible. If
    # z_i == 1, scenario i can be infeasible; if z_i == 0, it must be feasible.
    z = m.addMVar((data.num_scenarios,), vtype="B", name="z")

    add_constrs(data, alpha, no_vis, m, x, z)

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


def add_constrs(
    data: ProblemData, alpha: float, no_vis: bool, m: Model, x: MVar, z: MVar
):
    # At most alpha percent of the scenarios can be infeasible.
    m.addConstr(z.sum() <= alpha * data.num_scenarios, name="scenarios")

    # VALID INEQUALITIES ------------------------------------------------------

    if no_vis:  # do not add valid inequalities
        return

    sources = [data.edge_index_of((src, src)) for src in data.sources()]
    from_sources = [data.edge_indices_from(src) for src in data.sources()]
    from_sources = list(itertools.chain(*from_sources))  # type: ignore

    to_sinks = [data.edge_indices_to(sink) for sink in data.sinks()]
    to_sinks = list(itertools.chain(*to_sinks))  # type: ignore

    for scen in range(data.num_scenarios):
        src_capacity = np.array([src.supply[scen] for src in data.sources()])
        demand = sum(sink.demand[scen] for sink in data.sinks())

        # Source cuts.
        m.addConstr(src_capacity @ x[sources] >= demand * (1 - z[scen]))
        m.addConstr(x[from_sources].sum() >= demand * (1 - z[scen]))

        # Sink cut.
        m.addConstr(x[to_sinks].sum() >= demand * (1 - z[scen]))

        # Individual consumer demands, and the capacities of edges feeding
        # directly into that consumer.
        for sink in data.sinks():
            rhs = sink.demand[scen] * (1 - z[scen])
            m.addConstr(x[data.edge_indices_to(sink)].sum() >= rhs)

    # The capacity of any edge into a facility should not exceed the facility
    # capacity. Similarly, the capacity of the edges out of the facility should
    # not exceed the facility capacity. We take the worst-case capacities over
    # all scenarios to limit the number of constraints.
    for fac in data.facilities():
        # TODO also sources, other nodes?
        fac_edge_idx = data.edge_index_of((fac, fac))
        fac_edge = data.edges[fac_edge_idx]
        rhs = fac_edge.capacity.max() * x[fac_edge_idx]

        for to in data.edge_indices_to(fac):
            to_capacity = data.edges[to].capacity.max()
            m.addConstr(to_capacity * x[to] <= rhs)

        for frm in data.edge_indices_from(fac):
            frm_capacity = data.edges[frm].capacity.max()
            m.addConstr(frm_capacity * x[frm] <= rhs)
