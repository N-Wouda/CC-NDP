from typing import Dict, Type

from .BB import BB
from .DeterministicEquivalent import DeterministicEquivalent
from .Edge import Edge
from .FacilityNode import FacilityNode
from .FlowMIS import FlowMIS
from .MIS import MIS
from .MasterProblem import MasterProblem
from .Node import Node
from .ProblemData import ProblemData
from .Resource import Resource
from .Result import Result
from .RootResult import RootResult
from .SNC import SNC
from .SinkNode import SinkNode
from .SourceNode import SourceNode
from .SubProblem import SubProblem

FORMULATIONS: Dict[str, Type[SubProblem]] = {
    "BB": BB,
    "FlowMIS": FlowMIS,
    "MIS": MIS,
    "SNC": SNC,
}
