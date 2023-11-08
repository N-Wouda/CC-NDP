from .BB import BB as BB
from .FlowMIS import FlowMIS as FlowMIS
from .MIS import MIS as MIS
from .MasterProblem import MasterProblem as MasterProblem
from .ProblemData import ProblemData as ProblemData
from .SNC import SNC as SNC
from .SubProblem import SubProblem as SubProblem

FORMULATIONS: dict[str, type[SubProblem]] = {
    "BB": BB,
    "FlowMIS": FlowMIS,
    "MIS": MIS,
    "SNC": SNC,
}
