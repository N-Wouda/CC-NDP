"""
Makes the random instances used in the numerical experiments section of the
paper. See there for details.
"""

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from pathlib import Path

import numpy as np
from pyDOE2 import fullfact
from scipy.spatial import distance

from ccndp.classes import Edge, Node, ProblemData, SinkNode, SourceNode
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


def parameter_levels() -> dict[str, list]:
    return dict(
        num_nodes=[12, 24, 36],
        num_layers=[1, 2, 3],
        num_scen=[25, 50, 100, 200],
        num_res=[1, 2],
    )


def make_experiment(where, num_scen, num_nodes, num_layers, **kwargs):
    # Node data: supply (SourceNode), demand (SinkNode), and the node locations
    supply = np.around(np.random.uniform(50, 100, (num_nodes, num_scen)), 2)
    demand = np.around(np.random.uniform(0, 50, (num_nodes, num_scen)), 2)
    locs = np.around(np.random.uniform(0, 10, (3 * num_nodes, 2)), 2)

    # Node sets: sources, facilities, and sinks
    indices = np.arange(num_nodes, dtype=int)
    types = ["SUM"] * num_nodes

    sources = list(map(SourceNode, indices, locs, types, supply))

    fac_indices = num_nodes + indices
    fac_locs = locs[num_nodes:]
    facilities = list(map(Node, fac_indices, fac_locs, types))

    sink_indices = 2 * num_nodes + indices
    sink_locs = locs[2 * num_nodes :]
    sinks = list(map(SinkNode, sink_indices, sink_locs, types, demand))

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

    data = ProblemData(nodes=nodes, edges=edges, num_scenarios=num_scen)
    data.to_file(where)


def main():
    args = parse_args()

    np.random.seed(args.seed)
    args.experiment_dir.mkdir(exist_ok=True)

    levels = parameter_levels()
    num_levels = [len(level) for level in levels.values()]

    experiments = []

    with ThreadPoolExecutor() as executor:
        for num, design in enumerate(fullfact(num_levels), 1):
            exp = dict(index=num)

            for (k, v), idx in zip(levels.items(), design):
                exp[k] = v[int(idx)]

            where = args.experiment_dir / f"{num}.json"
            executor.submit(make_experiment, where, **exp)
            experiments.append(exp)

    with open(args.experiment_dir / "instances.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, ["index"] + list(levels.keys()))
        writer.writeheader()
        writer.writerows(experiments)


if __name__ == "__main__":
    main()
