from .Cut import Cut
from .Result import Result
from .SubProblem import SubProblem


class MasterProblem:
    """
    TODO
    """

    def __init__(self):
        pass

    def add_lazy_cut(self, cut: Cut):
        pass

    def solve_decomposition(self, subproblems: list[SubProblem]) -> Result:
        pass
