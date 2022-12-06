"""
Solves an instance to optimality. See the arguments (via ``run --help``) for
further information on the available options.
"""
from __future__ import annotations

import logging.config
from argparse import ArgumentParser

import numpy as np
import yaml  # type: ignore

# Must precede any imports, see https://stackoverflow.com/a/20280587.
with open("logging.yaml", "r") as file:
    log_settings = yaml.safe_load(file.read())
    logging.config.dictConfig(log_settings)

from src.classes import FORMULATIONS, ProblemData, Result, RootResult
from src.functions import create_master, create_subproblems


def parse_args():
    parser = ArgumentParser(prog="run")

    # General arguments for the entire program.
    parser.add_argument("data_loc", help="File system data location.")
    parser.add_argument("res_loc", help="File system result location.")
    parser.add_argument("seed", type=int, help="Seed for the PRNG.")
    parser.add_argument("alpha", type=float, help="Infeasibility parameter.")
    parser.add_argument(
        "--no_vis", action="store_true", help="Do not add valid inequalities."
    )

    subparsers = parser.add_subparsers(dest="command")

    # For the decomposition.
    decomp = subparsers.add_parser("decomp", help="Decomposition help.")
    decomp.set_defaults(func=run_decomp)

    decomp.add_argument(
        "formulation",
        choices=FORMULATIONS.keys(),
        help="Subproblem formulation.",
    )

    # For the root node/VI utility.
    root = subparsers.add_parser("root", help="Root node help.")
    root.set_defaults(func=run_root_relaxation)

    return parser.parse_args()


def run_decomp(master, subs) -> Result:
    return master.solve_decomposition(subs)


def run_root_relaxation(master, subs) -> RootResult:  # noqa: unused-argument
    return master.compute_root_relaxation()


def main():
    args = parse_args()
    np.random.seed(args.seed)

    data = ProblemData.from_file(args.data_loc)

    master = create_master(data, args.alpha, args.no_vis)
    subs = []

    if args.command == "decomp":  # only needed when solving the decomposition
        subs = create_subproblems(data, FORMULATIONS[args.formulation])

    res = args.func(master, subs)
    res.to_file(args.res_loc)
    print(res)


if __name__ == "__main__":
    main()
