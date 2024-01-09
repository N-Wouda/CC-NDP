"""
Ugly, one-off script that makes the single-commodity benchmark instances.
"""
import csv
import glob
from pathlib import Path

from src.classes.ProblemData import ProblemData


def main():
    experiments = []

    for loc in glob.glob("instances/r0[47]*.ndp"):
        data = ProblemData.from_file(loc)
        data = ProblemData(
            data.num_nodes,
            data.arcs,
            data.commodities[:1],
            data.probabilities,
        )

        data.to_file(f"instances/single-commodity/{Path(loc).name}")
        experiments.append(
            dict(
                name=f"{Path(loc).stem}",
                num_nodes=data.num_nodes,
                num_arcs=data.num_arcs,
                num_commodities=data.num_commodities,
                num_scenarios=data.num_scenarios,
            )
        )

    with open(
        "instances/single-commodity/instances.csv", "w", newline=""
    ) as fh:
        writer = csv.DictWriter(fh, list(experiments[0].keys()))
        writer.writeheader()
        writer.writerows(experiments)


if __name__ == "__main__":
    main()
