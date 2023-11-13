"""
Solves an instance to optimality. See the arguments (via ``solve --help``) for
further information on the available options.
"""
from __future__ import annotations

from argparse import ArgumentParser

from src.classes import FORMULATIONS, ProblemData, Result, RootResult
from src.functions import create_master, create_subproblems


def parse_args():
    parser = ArgumentParser(prog="solve")

    # General arguments for the entire program.
    parser.add_argument("data_loc", help="File system data location.")
    parser.add_argument("res_loc", help="File system result location.")
    parser.add_argument("alpha", type=float, help="Infeasibility parameter.")
    parser.add_argument(
        "--no_vis", action="store_true", help="Do not add valid inequalities."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # For the decomposition.
    decomp = subparsers.add_parser("decomp", help="Decomposition help.")
    decomp.set_defaults(func=run_decomp)
    decomp.add_argument(
        "formulation",
        choices=FORMULATIONS.keys(),
        help="Subproblem formulation.",
    )
    decomp.add_argument(
        "--with_combinatorial_cut",
        action="store_true",
        help="Also derive a combinatorial cut for each infeasible scenario.",
    )

    # For the root node/VI utility.
    root = subparsers.add_parser("root", help="Root node help.")
    root.set_defaults(func=run_root_relaxation)

    return parser.parse_args()


def run_decomp(data, master, args) -> Result:
    subs = create_subproblems(data, FORMULATIONS[args.formulation])
    return master.solve_decomposition(subs, args.with_combinatorial_cut)


def run_root_relaxation(data, master, args) -> RootResult:
    return master.compute_root_relaxation()


def main():
    args = parse_args()

    data = ProblemData.from_file(args.data_loc)
    master = create_master(data, args.alpha, args.no_vis)

    if res := args.func(data, master, args):
        res.to_file(args.res_loc)
        print(res)


if __name__ == "__main__":
    main()
