from gurobipy import Model

from src.classes import MasterProblem, ProblemData


def create_master(
    data: ProblemData, alpha: float, include_vi: bool
) -> MasterProblem:
    """
    TODO
    """
    m = Model()

    m.addMVar((data.num_edges,), obj=data.cost, vtype=data.vtype, name="x")

    z = m.addMVar((data.num_scenarios,), vtype="B", name="z")
    m.addConstr(z.sum() <= alpha * data.num_scenarios, name="scenarios")

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
