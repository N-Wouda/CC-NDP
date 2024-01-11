from dataclasses import dataclass

import numpy as np


@dataclass
class Cut:
    """
    Represents a new constraint that will be added to the master problem.

    The constraint has the following form:

        gamma * z[scen] >= gamma - beta @ y
    """

    beta: np.ndarray
    gamma: float
    scen: int
