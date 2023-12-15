"""
Ugly, one-off script that generates the experimental benchmark instances.
"""
import csv
import glob
import pathlib

from src.classes import ProblemData


def parse_scen(where: str):
    with open(where) as fh:
        lines = iter(fh.readlines())

    next(lines)  # = num scenarios, but we already get that from the data

    for line in lines:
        prob, *demands = map(float, line.strip().split())
        yield prob, demands


def make_problem_data(data: ProblemData, scenarios):
    for prob, demands in scenarios:
        data.probabilities.append(prob)
        for commodity, demand in zip(data.commodities, demands):
            commodity.demands.append(demand)


def main():
    experiments = []

    for ndp in glob.glob("instances/base/*.ndp"):
        ndp = pathlib.Path(ndp)
        group, typ = ndp.stem.split(".")

        for scen in glob.glob(f"instances/scenarios/{group}-0-*"):
            _, corr, size = scen.split("-")

            if size == "1000":
                scens = [(prob, demands) for prob, demands in parse_scen(scen)]

                data = ProblemData.from_file(ndp)
                scens_128 = [(1 / 128, demands) for _, demands in scens[:128]]
                make_problem_data(data, scens_128)
                experiments.append(
                    dict(
                        name=f"{group}-{typ}-{corr}-128",
                        group=group,
                        correlation=corr,
                        num_nodes=data.num_nodes,
                        num_arcs=data.num_arcs,
                        num_commodities=data.num_commodities,
                        num_scenarios=data.num_scenarios,
                    )
                )
                data.to_file(f"instances/{group}-{typ}-{corr}-128.ndp")

                data = ProblemData.from_file(ndp)
                scens_256 = [
                    (1 / 256, demands) for _, demands in scens[128:384]
                ]
                make_problem_data(data, scens_256)
                experiments.append(
                    dict(
                        name=f"{group}-{typ}-{corr}-256",
                        group=group,
                        correlation=corr,
                        num_nodes=data.num_nodes,
                        num_arcs=data.num_arcs,
                        num_commodities=data.num_commodities,
                        num_scenarios=data.num_scenarios,
                    )
                )
                data.to_file(f"instances/{group}-{typ}-{corr}-256.ndp")

                data = ProblemData.from_file(ndp)
                scens_512 = [
                    (1 / 512, demands) for _, demands in scens[384:896]
                ]
                make_problem_data(data, scens_512)
                experiments.append(
                    dict(
                        name=f"{group}-{typ}-{corr}-512",
                        group=group,
                        correlation=corr,
                        num_nodes=data.num_nodes,
                        num_arcs=data.num_arcs,
                        num_commodities=data.num_commodities,
                        num_scenarios=data.num_scenarios,
                    )
                )
                data.to_file(f"instances/{group}-{typ}-{corr}-512.ndp")
            else:
                data = ProblemData.from_file(ndp)
                make_problem_data(data, parse_scen(scen))

                experiments.append(
                    dict(
                        name=f"{group}-{typ}-{corr}-{size}",
                        group=group,
                        correlation=corr,
                        num_nodes=data.num_nodes,
                        num_arcs=data.num_arcs,
                        num_commodities=data.num_commodities,
                        num_scenarios=data.num_scenarios,
                    )
                )
                data.to_file(f"instances/{group}-{typ}-{corr}-{size}.ndp")

        for scen in glob.glob(f"instances/scenarios/{group}-0.2-*"):
            _, corr, size = scen.split("-")

            if size == "1000":
                scens = [(prob, demands) for prob, demands in parse_scen(scen)]

                data = ProblemData.from_file(ndp)
                scens_128 = [(1 / 128, demands) for _, demands in scens[:128]]
                make_problem_data(data, scens_128)
                experiments.append(
                    dict(
                        name=f"{group}-{typ}-{corr}-128",
                        group=group,
                        correlation=corr,
                        num_nodes=data.num_nodes,
                        num_arcs=data.num_arcs,
                        num_commodities=data.num_commodities,
                        num_scenarios=data.num_scenarios,
                    )
                )
                data.to_file(f"instances/{group}-{typ}-{corr}-128.ndp")

                data = ProblemData.from_file(ndp)
                scens_256 = [
                    (1 / 256, demands) for _, demands in scens[128:384]
                ]
                make_problem_data(data, scens_256)
                experiments.append(
                    dict(
                        name=f"{group}-{typ}-{corr}-256",
                        group=group,
                        correlation=corr,
                        num_nodes=data.num_nodes,
                        num_arcs=data.num_arcs,
                        num_commodities=data.num_commodities,
                        num_scenarios=data.num_scenarios,
                    )
                )
                data.to_file(f"instances/{group}-{typ}-{corr}-256.ndp")

                data = ProblemData.from_file(ndp)
                scens_512 = [
                    (1 / 512, demands) for _, demands in scens[384:896]
                ]
                make_problem_data(data, scens_512)
                experiments.append(
                    dict(
                        name=f"{group}-{typ}-{corr}-512",
                        group=group,
                        correlation=corr,
                        num_nodes=data.num_nodes,
                        num_arcs=data.num_arcs,
                        num_commodities=data.num_commodities,
                        num_scenarios=data.num_scenarios,
                    )
                )
                data.to_file(f"instances/{group}-{typ}-{corr}-512.ndp")
            else:
                data = ProblemData.from_file(ndp)
                make_problem_data(data, parse_scen(scen))
                experiments.append(
                    dict(
                        name=f"{group}-{typ}-{corr}-{size}",
                        group=group,
                        correlation=corr,
                        num_nodes=data.num_nodes,
                        num_arcs=data.num_arcs,
                        num_commodities=data.num_commodities,
                        num_scenarios=data.num_scenarios,
                    )
                )
                data.to_file(f"instances/{group}-{typ}-{corr}-{size}.ndp")

    with open("instances/instances.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, list(experiments[0].keys()))
        writer.writeheader()
        writer.writerows(experiments)


if __name__ == "__main__":
    main()
