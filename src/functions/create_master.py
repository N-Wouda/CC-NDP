from gurobipy import Model

from src.classes import MasterProblem, ProblemData


def create_master(
    data: ProblemData, alpha: float, include_vi: bool
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
    include_vi
        Whether to include the valid inequalities (VI's) in the model. These
        are not strictly needed, but help the formulation solve much faster.

    Returns
    -------
    MasterProblem
        The created master problem instance.
    """
    m = Model()

    # Construction decision variables, with costs and variable types as given
    # by the problem instance.
    x = m.addMVar((data.num_edges,), obj=data.cost, vtype=data.vtype, name="x")

    # The z variables decide which of the scenarios must be made feasible. If
    # z_i == 1, scenario i can be infeasible; if z_i == 0, it must be feasible.
    # At most alpha percent of the scenarios can be infeasible.
    z = m.addMVar((data.num_scenarios,), vtype="B", name="z")
    m.addConstr(z.sum() <= alpha * data.num_scenarios, name="scenarios")

    if include_vi:  # add valid inequalities to the master problem formulation
        pass  # TODO vi's

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
