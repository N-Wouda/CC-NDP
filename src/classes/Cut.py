from dataclasses import dataclass

import numpy as np


@dataclass
class Cut:
    beta: np.ndarray
    gamma: float
