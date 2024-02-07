import numpy as np
from gurobipy import MVar, Model

from src.classes.ProblemData import ProblemData


def create_sub_model(
    data: ProblemData,
    demands: np.ndarray[int],
    model: Model = None,
    y: MVar = None,
) -> Model:
    """
    Creates a second-stage model, optionally using a given first-stage model
    to add the second stage to.
    """
    if model is None:
        m = Model()
        y: MVar = m.addMVar((data.num_arcs,), name="y")  # type: ignore
    else:
        m = model

    x = m.addMVar((data.num_arcs, data.num_commodities), name="x")  # 2nd stage

    # Capacity constraints.
    for idx, arc in enumerate(data.arcs):
        # All flow through an arc must not exceed the arc's capacity.
        lhs = x[idx, :].sum()
        rhs = arc.capacity * y[idx]
        m.addConstr(lhs <= rhs, name=f"capacity{arc}")

    # Balance constraints.
    for commodity_idx, commodity in enumerate(data.commodities):
        for node in range(1, data.num_nodes + 1):
            frm = x[data.arc_indices_from(node), commodity_idx].sum()
            to = x[data.arc_indices_to(node), commodity_idx].sum()

            if node == commodity.to_node:  # is the commodity destination
                name = f"demand{node, commodity_idx}"
                m.addConstr(to >= demands[commodity_idx], name=name)
            elif node != commodity.from_node:  # is a regular intermediate node
                name = f"balance{node, commodity_idx}"
                m.addConstr(to == frm, name=name)

        # Remove superfluous flows: those out of the destination, or into the
        # origin. These must be set to zero, and can thus be removed from the
        # model.
        m.remove(x[data.arc_indices_to(commodity.from_node), commodity_idx])
        m.remove(x[data.arc_indices_from(commodity.to_node), commodity_idx])

    m.update()
    return m
