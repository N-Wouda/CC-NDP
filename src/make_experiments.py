"""
Makes the random instances used in the numerical experiments section of the
paper. See there for details.
"""

import csv
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
from pyDOE2 import fullfact

from src.classes import Node, ProblemData, SourceNode, SinkNode


def parameter_levels() -> dict[str, list[Any]]:
    num_nodes = [12, 24, 36]
    num_layers = [1, 2, 3]
    num_scen = [25, 50, 100, 200]

    return locals()


def make_and_write_experiment(
    index: int, num_scen: int, num_nodes: int, num_layers: int
):
    # TODO make nodes
    nodes = []

    # TODO edges, demands, (fix + var) capacities
    edges = []
    demands = np.array([])

    fix_capacities = np.array([])
    var_capacities = np.array([])

    data = ProblemData(
        nodes=nodes,
        edges=edges,
        fix_capacities=fix_capacities,
        var_capacities=var_capacities,
        demands=demands,
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
