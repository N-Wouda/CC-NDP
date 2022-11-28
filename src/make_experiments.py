"""
Makes the random instances used in the numerical experiments section of the
paper. See there for details.
"""

import csv
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


def make_and_write_experiment(num: int, exp: dict[str, Any]):
    # TODO
    num_scen = exp["num_scen"]
    num_src = num_cons = num_fac = exp["num_nodes"]
    num_layers = exp["num_layers"]

    supply = np.random.uniform(50, 100, (num_scen, num_src))
    demand = np.random.uniform(0, 50, (num_scen, num_cons))

    # TODO merge supply and demand and edge capacities

    cost_src = 5 * np.mean(supply, axis=0)
    cost_fac = np.random.uniform(5, 10, num_fac)

    locs = np.random.uniform(0, 10, (exp["num_nodes"], 2))

    def make_edges() -> list[tuple]:
        E = []

        for layer in range(num_layers):
            fac = np.arange(num_fac // num_layers, dtype=int)

            if layer == 0:  # sources to first layer
                src = np.arange(num_src, dtype=int)
                E += product(src, num_src + fac)

            if layer > 0:  # previous layer to this layer
                E += product(
                    (num_src + ((layer - 1) * len(fac))) + fac,
                    (num_src + (layer * len(fac))) + fac,
                )

            if layer == num_layers - 1:  # final layer to sinks
                cons = np.arange(num_cons, dtype=int)
                E += product(
                    (num_src + (layer * len(fac))) + fac,
                    (num_src + num_fac) + cons,
                )

        return E

    edges = make_edges()
    loc_pairs = [(locs[i], locs[j]) for i, j in edges]
    cost_edge = [distance.euclidean(*loc) for loc in loc_pairs]

    # TODO all edges + facilities (as edges)
    cost = ...

    data = ProblemData(
        nodes, locs, edges, demand, capacity, cost, vtype, num_scen
    )

    data.to_file(f"data/instances/{num}.json")


def main():
    np.random.seed(42)

    levels = parameter_levels()
    num_levels = [len(level) for level in levels.values()]

    experiments = []

    with ThreadPoolExecutor() as executor:
        for num, design in enumerate(fullfact(num_levels), 1):
            exp = {
                key: value[int(idx)]
                for (key, value), idx in zip(levels.items(), design)
            }

            exp["index"] = num

            executor.submit(make_and_write_experiment, num, exp)
            experiments.append(exp)

    with open("data/instances/instances.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, ["index"] + list(levels.keys()))
        writer.writeheader()
        writer.writerows(experiments)


if __name__ == "__main__":
    main()
