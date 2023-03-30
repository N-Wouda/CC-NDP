"""
Makes the random instances used in the numerical experiments section of the
paper. See there for details.
"""

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
from itertools import count, cycle, product
from pathlib import Path

import numpy as np
from pyDOE2 import fullfact
from scipy.spatial import distance

from ccndp.classes import Edge
from ccndp.classes import FacilityNode as Facility
from ccndp.classes import ProblemData, Resource
from ccndp.classes import SinkNode as Sink
from ccndp.classes import SourceNode as Source
from ccndp.functions import pairwise


def parse_args():
    parser = argparse.ArgumentParser(prog="make_experiments")

    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--experiment_dir",
        help="Location to write experiments. Will be created if not exists.",
        default="data/instances/",
        type=Path,
    )

    return parser.parse_args()


def make_experiment_settings():
    levels = dict(
        num_nodes=[12, 24, 36],
        num_layers=[1, 2],
        num_scen=[25, 50, 100, 200],
        num_res=[0, 1, 2, 3],
    )

    num_levels = [len(level) for level in levels.values()]
    exp_number = count(1)

    experiments = []

    for design in fullfact(num_levels):
        exp = {}

        for (k, v), idx in zip(levels.items(), design):
            exp[k] = v[int(idx)]

        # With just one layer, we have source -> facility -> sink, so there's
        # no resources other than the source and sink resources.
        if exp["num_res"] > 0 and exp["num_layers"] == 1:
            continue

        # With more than one layer, we have source -> facility1 -> facility2
        # -> sink, so there is at least one resource needed between facility1
        # and facility2 (and possibly more)
        if exp["num_res"] == 0 and exp["num_layers"] == 2:
            continue

        exp["index"] = next(exp_number)
        experiments.append(exp)

    return experiments


def make_experiment(where, num_scen, num_nodes, num_layers, num_res, **kwargs):
    resources = [
        Resource(0, "Source resource"),
        *[Resource(idx, f"Res #{idx}") for idx in range(1, num_res + 1)],
        Resource(num_res + 1, "Sink resource"),
    ]

    # Node data: supply (SourceNode), demand (SinkNode), and the node locations
    supply = np.around(np.random.uniform(100, 200, (num_nodes, num_scen)), 2)
    demand = np.around(np.random.uniform(0, 50, (num_nodes, num_scen)), 2)
    locs = np.around(np.random.uniform(0, 10, (3 * num_nodes, 2)), 2)

    # Node sets: sources, facilities, and sinks, and what they make and need.
    src_idcs = np.arange(num_nodes, dtype=int)
    src_makes = [resources[0] for _ in range(num_nodes)]
    sources = list(map(Source, src_idcs, locs, src_makes, supply))

    fac_idcs = num_nodes + src_idcs
    fac_locs = locs[num_nodes:]

    if num_layers == 1:
        assert num_res == 0
        fac_makes = [resources[-1] for _ in range(num_nodes)]
        fac_needs = [(resources[0],) for _ in range(num_nodes)]
    elif num_layers == 2:
        assert num_res > 0
        products = resources[1:-1]
        products_cycle = cycle(products)

        # First half of the facilities makes products (in the first layer)
        # using the source resource.
        fac_makes = [next(products_cycle) for _ in range(num_nodes // 2)]
        fac_needs = [(resources[0],) for _ in range(num_nodes // 2)]

        # The second half of the facilities (in the second layer) makes the
        # sink resource using products created in the first layer.
        fac_makes += [resources[-1] for _ in range(num_nodes // 2)]
        fac_needs += [tuple(products) for _ in range(num_nodes // 2)]
    else:
        raise ValueError("num_layers is not in {1, 2}!")

    facilities = list(map(Facility, fac_idcs, fac_locs, fac_makes, fac_needs))

    sink_idcs = 2 * num_nodes + src_idcs
    sink_locs = locs[2 * num_nodes :]
    sink_needs = [resources[-1] for _ in range(num_nodes)]
    sinks = list(map(Sink, sink_idcs, sink_locs, sink_needs, demand))

    nodes = sources + facilities + sinks

    layers = np.array_split(facilities, num_layers)

    # Edges. First we construct all source and a facility edges. These
    # represent the construction decisions at the nodes.
    edges = []

    for src in sources:
        capacity = supply[src.idx]
        cost = 5 * capacity.mean()
        edges.append(Edge(src, src, cost, capacity, "B"))

    for fac in facilities:
        capacity = np.ones((num_scen,))
        cost = np.random.uniform(5, 10)
        edges.append(Edge(fac, fac, cost, capacity, "C"))

    # Now we connect all nodes together with edges.
    for out_layer, in_layer in pairwise([sources, *layers, sinks]):
        for frm, to in product(out_layer, in_layer):
            capacity = np.ones((num_scen,))
            cost = distance.euclidean(frm.loc, to.loc)
            edges.append(Edge(frm, to, cost, capacity, "C"))

    data = ProblemData(
        resources=resources, nodes=nodes, edges=edges, num_scenarios=num_scen
    )

    data.to_file(where)


def main():
    args = parse_args()
    np.random.seed(args.seed)
    args.experiment_dir.mkdir(exist_ok=True)

    experiments = make_experiment_settings()

    with ThreadPoolExecutor() as executor:
        for num, exp in enumerate(experiments, 1):
            where = args.experiment_dir / f"{num}.json"
            executor.submit(make_experiment, where, **exp)

    with open(args.experiment_dir / "instances.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, list(experiments[0].keys()))
        writer.writeheader()
        writer.writerows(experiments)


if __name__ == "__main__":
    main()
