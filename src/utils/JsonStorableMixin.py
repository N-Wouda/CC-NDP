from __future__ import annotations

import json
from abc import ABC

from .JsonDecoder import JsonDecoder
from .JsonEncoder import JsonEncoder


class JsonStorableMixin(ABC):
    """
    JsonStorableMixin is a mixin class that provides methods to save and load
    (ProblemData) classes to and from the filesystem, where they are stored as
    JSON files.

    This class, in particular, also helps with reading/writing Node and Edge
    lists, and numpy arrays.
    """

    @classmethod
    def from_file(cls, loc: str, decoder=JsonDecoder) -> JsonStorableMixin:
        """
        Reads an object from the given location. Assumes the data at the given
        location are JSON-formatted.
        """
        with open(loc, "r") as fh:
            raw = json.load(fh, cls=decoder)

        return cls(**raw)  # type: ignore

    def to_file(self, loc: str, encoder=JsonEncoder):
        """
        Writes this object as JSON to the given location on the filesystem.
        """
        with open(loc, "w") as fh:
            json.dump(vars(self), fh, cls=encoder)
