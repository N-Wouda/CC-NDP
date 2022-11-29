from argparse import ArgumentParser

import matplotlib.pyplot as plt
import numpy as np

from src.classes import ProblemData, Result


def parse_args():
    parser = ArgumentParser(prog="plot")

    # General arguments for the entire program.
    parser.add_argument("data_loc", help="File system data location.")
    parser.add_argument("res_loc", help="File system result location.")

    return parser.parse_args()


def plot(data: ProblemData, res: Result):
    # TODO
    _, ax = plt.subplots(figsize=(12, 12))

    node2idx = {node: idx for idx, node in enumerate(data.nodes)}
    marker_size = 144

    sources = []
    facilities = []

    for (k, v), (frm, to) in zip(res.decisions.items(), data.edges):
        if not np.isclose(v, 0.0):
            from_node = frm.split("-")[0]
            to_node = to.split("-")[0]

            if from_node == to_node:
                if from_node.startswith("source"):
                    sources.append(node2idx[from_node])
                else:
                    facilities.append(node2idx[from_node])
                    annotate(ax, [v], [data.locs[node2idx[from_node]]])
            else:
                locs = [node2idx[from_node], node2idx[to_node]]
                x, y = data.locs[locs, 0], data.locs[locs, 1]
                ax.plot(x, y, linewidth=1, color="tab:blue")
                annotate(ax, [v], [np.array([np.mean(x), np.mean(y)])])

    ax.scatter(
        data.locs[sources, 0],
        data.locs[sources, 1],
        marker_size,
        c="black",
        marker="^",
        zorder=2.5,
        label="Source facilities",
    )

    ax.scatter(
        data.locs[facilities, 0],
        data.locs[facilities, 1],
        marker_size,
        c="red",
        marker="o",
        zorder=2.5,
        label="Facilities",
    )

    sink_idcs = [node2idx[node] for node in data.sink_nodes]
    ax.scatter(
        data.locs[sink_idcs, 0],
        data.locs[sink_idcs, 1],
        marker_size,
        c="green",
        marker="s",
        zorder=2.5,
        label="Consumers",
    )

    annotate(ax, data.demand.mean(axis=0), data.locs[sink_idcs])

    ax.tick_params(
        bottom=False, labelbottom=False, left=False, labelleft=False
    )

    ax.set_title("Construction decisions", fontsize=20)
    ax.legend(frameon=False, fontsize=14, ncol=3, loc="lower center")

    plt.tight_layout()
    plt.show()


def annotate(ax: plt.Axes, items: np.array, locations: np.array):
    style = dict(bbox=dict(boxstyle="round", fc="w"), fontsize=8)

    for i, (loc, num) in enumerate(zip(locations, items)):
        if not np.isclose(num, 0.0):
            ax.annotate(f"{num:.1f}", loc + 0.05, **style)


def main():
    args = parse_args()

    data = ProblemData.from_file(args.data_loc)
    res = Result.from_file(args.res_loc)

    print(res)
    plot(data, res)


if __name__ == "__main__":
    main()
