from argparse import ArgumentParser

import matplotlib.pyplot as plt

from src.classes import ProblemData, Result


def parse_args():
    parser = ArgumentParser(prog="plot")

    # General arguments for the entire program.
    parser.add_argument("data_loc", help="File system data location.")
    parser.add_argument("res_loc", help="File system result location.")

    return parser.parse_args()


def plot(data: ProblemData, res: Result):
    size = 2.5
    fig = plt.figure(figsize=(9 * size, 6 * size))
    gs = plt.GridSpec(6, 9, figure=fig)

    data.plot_solution(res, ax=fig.add_subplot(gs[:6, :6]))  # [0, 6] x [0, 6]
    res.plot_convergence(ax=fig.add_subplot(gs[:2, 6:]))  # [0, 2] x [6, 9]
    res.plot_runtimes(ax=fig.add_subplot(gs[2:4, 6:]))  # [2, 4] x [6, 9]

    plt.show()


def main():
    args = parse_args()

    data = ProblemData.from_file(args.data_loc)
    res = Result.from_file(args.res_loc)

    print(res)
    plot(data, res)


if __name__ == "__main__":
    main()
