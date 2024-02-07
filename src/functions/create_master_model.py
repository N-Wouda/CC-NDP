import numpy as np
from gurobipy import Model

from src.classes.ProblemData import ProblemData

from .create_sub_model import create_sub_model


def create_master_model(
    data: ProblemData,
    alpha: float,
    without_master_scenario: bool,
) -> Model:
    """
    Creates a first-stage model.
    """
    m = Model()

    # Construction decision variables, with costs and variable types as given
    # by the problem instance.
    y = m.addMVar(
        (data.num_arcs,),
        obj=[arc.fixed_cost for arc in data.arcs],  # type: ignore
        vtype="B",  # type: ignore
        name=[str(arc) for arc in data.arcs],
    )

    # The z variables decide which of the scenarios must be made feasible. If
    # z_i == 1, scenario i can be infeasible; if z_i == 0, it must be feasible.
    z = m.addMVar((data.num_scenarios,), vtype="B", name="z")

    # At most alpha percent of the scenarios can be infeasible.
    m.addConstr(z.sum() <= alpha * data.num_scenarios, name="scenarios")

    if not without_master_scenario and not np.isclose(alpha, 1):
        # This constructed scenario is essentially the chance-constrained
        # equivalent of the expected value scenario, and it is valid by a
        # suitable adaptation of Lemma 1 of Crainic et al. (2021)'s partial
        # Benders decomposition paper.
        scen_demands = []
        for c in data.commodities:
            quantile = np.quantile(c.demands, 1 - alpha, method="higher")
            sum_below = np.sum(c.demands, where=c.demands <= quantile)
            scen_demands.append(sum_below / data.num_scenarios)

        create_sub_model(data, scen_demands, m, y)  # create into given model

    m.update()
    return m
