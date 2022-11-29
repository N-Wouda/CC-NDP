"""
Makes the random instances used in the numerical experiments section of the
paper. See there for details.
"""

import csv
import re
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from typing import Any

import numpy as np
from pyDOE2 import fullfact
from scipy.spatial import distance

from src.classes import ProblemData


def parameter_levels() -> dict[str, list[Any]]:
    num_nodes = [12, 24, 36]
    num_layers = [1, 2, 3]
    num_scen = [25, 50, 100, 200]

    return locals()


def make_and_write_experiment(
    index: int, num_scen: int, num_nodes: int, num_layers: int
):
    locs = np.random.uniform(0, 10, (3 * num_nodes, 2))
    nodes = np.array(
        [
            f"{prefix}{node_idx}"
            for prefix in ["source", "facility", "sink"]
            for node_idx in range(num_nodes)
        ]
    )

    sources, facilities, sinks = np.split(nodes, 3)
    layers = np.split(facilities, num_layers)

    # These edges represent the facilities we construct at the nodes. Each node
    # is represented as an ("in", "out") edge.
    edges = []
    edges += [(f"{src}-in", f"{src}-out") for src in sources]
    edges += [(f"{fac}-in", f"{fac}-out") for fac in facilities]

    # Edges connecting the source nodes to the first layer of facilities.
    if num_layers >= 1:
        src_nodes_out = [f"{src}-out" for src in sources]
        first_layer_in = [f"{fac}-in" for fac in layers[0]]
        edges += product(src_nodes_out, first_layer_in)

    # Edges connecting the facility layers (second layer if given)
    if num_layers >= 2:
        first_layer_out = [f"{fac}-out" for fac in layers[0]]
        second_layer_in = [f"{fac}-in" for fac in layers[1]]
        edges += product(first_layer_out, second_layer_in)

    # Edges connecting the facility layers (third layer if given)
    if num_layers >= 3:
        second_layer_out = [f"{fac}-out" for fac in layers[1]]
        third_layer_in = [f"{fac}-in" for fac in layers[2]]
        edges += product(second_layer_out, third_layer_in)

    # Edges connecting the final layer to the sink nodes.
    last_layer_out = [f"{fac}-out" for fac in layers[-1]]
    sinks_in = [f"{sink}-in" for sink in sinks]
    edges += product(last_layer_out, sinks_in)

    # Unit capacity everywhere except for the source nodes, which have a
    # uniform capacity in [50, 100].
    capacity = np.ones((num_scen, len(edges)))
    capacity[:, :num_nodes] = np.random.uniform(50, 100, (num_scen, num_nodes))

    # Costs, per edge. This depends on the type of edge:
    #  * Source node: 5 * <mean supply>.
    #  * Facilities: Uniform[5, 10].
    #  * Edge: Euclidean distance between end points.
    costs = []

    for frm, to in edges:
        frm_match = re.search(r"\d+", frm)
        to_match = re.search(r"\d+", to)

        if not frm_match or not to_match:
            raise ValueError(f"Pair ({frm}, {to}) not understood.")

        frm_num = int(frm_match[0])
        to_num = int(to_match[0])

        # Source node facility.
        if frm.startswith("source") and to.startswith("source"):
            assert frm_num == to_num
            costs.append(5 * np.mean(capacity[:, frm_num]))

        # Edge from source to facility.
        if frm.startswith("source") and to.startswith("facility"):
            frm_loc = locs[frm_num]
            to_loc = locs[num_nodes + to_num]
            costs.append(distance.euclidean(frm_loc, to_loc))

        # Either a facility, or an edge between facilities.
        if frm.startswith("facility") and to.startswith("facility"):
            if frm_num == to_num:  # facility
                costs.append(np.random.uniform(5, 10))
            else:  # edge
                frm_loc = locs[num_nodes + frm_num]
                to_loc = locs[num_nodes + to_num]
                costs.append(distance.euclidean(frm_loc, to_loc))

        # Edge from facility to a sink.
        if frm.startswith("facility") and to.startswith("sink"):
            frm_loc = locs[num_nodes + frm_num]
            to_loc = locs[2 * num_nodes + to_num]
            costs.append(distance.euclidean(frm_loc, to_loc))

    # Continuous everywhere, except for the source nodes, which are binary.
    vtype = np.full((len(edges),), fill_value="C")
    vtype[:num_nodes] = "B"

    data = ProblemData(
        nodes=nodes,
        locs=locs,
        edges=np.array(edges),
        demand=np.random.uniform(0, 50, (num_scen, num_nodes)),
        capacity=capacity,
        cost=np.array(costs),
        vtype=vtype,
        num_scenarios=num_scen,
    )

    data.to_file(f"data/instances/{index}.json")


def main():
    np.random.seed(42)

    levels = parameter_levels()
    num_levels = [len(level) for level in levels.values()]

    experiments = []

    with ThreadPoolExecutor() as executor:
        for num, design in enumerate(fullfact(num_levels), 1):
            exp = dict(index=num)

            for (k, v), idx in zip(levels.items(), design):
                exp[k] = v[int(idx)]

            executor.submit(make_and_write_experiment, **exp)
            experiments.append(exp)

    with open("data/instances/instances.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, ["index"] + list(levels.keys()))
        writer.writeheader()
        writer.writerows(experiments)


if __name__ == "__main__":
    main()
