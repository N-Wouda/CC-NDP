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

    # TODO these need to be updated with eta/node types (see also other repo
    #  for some pointers on how to do that).

    if no_vis:  # do not add valid inequalities
        return

    for src in data.sources():
        src_edge_idx = data.edge_index_of((src, src))

        for edge_idx in data.edge_indices_from(src):
            # There is no point in having an edge with capacity when the source
            # has not been built.
            m.addConstr(
                x[edge_idx] <= src.supply.max() * x[src_edge_idx],
                name=f"{src} supply",
            )

    for fac in data.facilities():
        fac_edge_idx = data.edge_index_of((fac, fac))
        edge_indices_from_fac = data.edge_indices_from(fac)
        edge_indices_to_fac = data.edge_indices_to(fac)

        # Facility capacity should not exceed inflow along edges.
        m.addConstr(
            x[fac_edge_idx] <= x[edge_indices_to_fac].sum(),
            name="facility agg inflow",
        )

        for edge_idx in edge_indices_to_fac:
            # Similarly, an individual edge should not exceed the capacity of
            # the facility target.
            m.addConstr(x[edge_idx] <= x[fac_edge_idx], name="facility inflow")

        # Facility capacity should not exceed outflow along edges.
        m.addConstr(
            x[fac_edge_idx] <= x[edge_indices_from_fac].sum(),
            name="facility agg outflow",
        )

        for edge_idx in edge_indices_from_fac:
            # Similarly, an edge need not be bigger than the attached facility.
            m.addConstr(
                x[edge_idx] <= x[fac_edge_idx], name="facility outflow"
            )

    for sink in data.sinks():
        edge_indices_to_sink = data.edge_indices_to(sink)

        for edge_idx in edge_indices_to_sink:
            # There is no point in having individual edges capacities exceeding
            # the demand they need to supply.
            m.addConstr(x[edge_idx] <= sink.demand.max(), name="sink demand")

        for scen in range(data.num_scenarios):
            # All edges into customers should together be sufficient to meet
            # demand at the consumer in each feasible scenario.
            d = sink.demand[scen]
            m.addConstr(
                x[edge_indices_to_sink].sum() >= (1 - z[scen]) * d,
                name="sink edge capacity",
            )

    for scen in range(data.num_scenarios):
        supply = np.array([src.supply[scen] for src in data.sources()])
        src_idcs = [data.edge_index_of((src, src)) for src in data.sources()]
        lhs = supply @ x[src_idcs]

        demand = sum(sink.demand[scen] for sink in data.sinks())
        rhs = (1 - z[scen]) * demand

        # We need at least enough source production to meet demand in each
        # scenario we make feasible.
        m.addConstr(lhs >= rhs, name=f"scen[{scen}] supply")

    # TODO layer capacity (see other repository for some pointers)
