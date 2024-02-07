import numpy as np
from gurobipy import MVar, Model

from src.classes.ProblemData import ProblemData

from .create_sub_model import create_sub_model


def create_master_model(
    data: ProblemData,
    alpha: float,
    no_vis: bool,
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

    if not no_vis:
        _add_vis(data, alpha, m, y, z)

    if not without_master_scenario and not np.isclose(alpha, 1):
        # Then we add an artificial scenario that must first be made feasible.
        # This scenario has the average demands of each commodity's demand
        # that is less than its marginal (1 - alpha)-quantile. This is
        # essentially the chance-constrained equivalent of the mean value
        # scenario, and it is valid by a suitable adaptation of Lemma 1 of
        # Crainic et al. (2021)'s partial Benders decomposition paper.
        demands = []
        for c in data.commodities:
            quantile = np.quantile(c.demands, 1 - alpha, method="higher")
            demands.append(np.mean(c.demands, where=c.demands <= quantile))

        create_sub_model(data, demands, m, y)  # create into given model

    m.update()
    return m


def _add_vis(data: ProblemData, alpha: float, m: Model, y: MVar, z: MVar):
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
