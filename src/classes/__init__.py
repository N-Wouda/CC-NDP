from .ProblemData import ProblemData as ProblemData
from .BB import BB as BB
from .FlowMIS import FlowMIS as FlowMIS
from .MIS import MIS as MIS
from .SNC import SNC as SNC
from .SubProblem import SubProblem as SubProblem
from .MasterProblem import MasterProblem as MasterProblem


FORMULATIONS: dict[str, type[SubProblem]] = {
    "BB": BB,
    "FlowMIS": FlowMIS,
    "MIS": MIS,
    "SNC": SNC,
}
