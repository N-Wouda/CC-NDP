from typing import Type

from src.classes import ProblemData, SubProblem


def create_subproblems(
    data: ProblemData, cls: Type[SubProblem]
) -> list[SubProblem]:
    """
    Creates the subproblems.

    Parameters
    ----------
    data
        Problem data instance.
    cls
        Type of subproblem formulation to use.

    Returns
    -------
    list
        List of created subproblems. These are instance of the ``cls`` passed
        into this function.
    """
    subs = []

    for scen in range(data.num_scenarios):
        # TODO
        #         T: csr_matrix,
        #         W: csr_matrix,
        #         h: list[float] | np.array,
        #         senses: list[str] | np.array,
        #         vname: list[str],
        #         cname: list[str],
        #         scen: int,
        T = ...
        W = ...
        h = ...
        senses = ...
        vname = ...
        cname = ...

        subs.append(cls(T, W, h, senses, vname, cname, scen))

    return subs
