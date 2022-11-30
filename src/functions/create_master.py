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
        obj=data.cost,  # type: ignore
        vtype=data.vtype,  # type: ignore
        name=[f"x[{frm}, {to}]" for frm, to in data.edges],  # type: ignore
    )

    # The z variables decide which of the scenarios must be made feasible. If
    # z_i == 1, scenario i can be infeasible; if z_i == 0, it must be feasible.
    z = m.addMVar((data.num_scenarios,), vtype="B", name="z")

    add_constrs(m, data, alpha, no_vis, x, z)

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
    m: Model, data: ProblemData, alpha: float, no_vis: bool, x: MVar, z: MVar
):
    # At most alpha percent of the scenarios can be infeasible.
    m.addConstr(z.sum() <= alpha * data.num_scenarios, name="scenarios")

    # VALID INEQUALITIES ------------------------------------------------------

    if no_vis:  # do not add valid inequalities
        return

    # TODO add VI's from other repo
