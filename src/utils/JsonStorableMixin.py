from __future__ import annotations

import json
from abc import ABC

from .NumpyJsonDecoder import NumpyJsonDecoder
from .NumpyJsonEncoder import NumpyJsonEncoder


class JsonStorableMixin(ABC):
    """
    JsonStorableMixin is a mixin class that provides methods to save and load
    classes to and from the filesystem, where they are stored as JSON files.
    """

    @classmethod
    def from_file(
        cls, loc: str, decoder=NumpyJsonDecoder
    ) -> JsonStorableMixin:
        """
        Reads an object from the given location. Assumes the data at the given
        location are JSON-formatted.
        """
        with open(loc, "r") as fh:
            raw = json.load(fh, cls=decoder)

        return cls(**raw)  # type: ignore

    def to_file(self, loc: str, encoder=NumpyJsonEncoder):
        """
        Writes this object as a JSON file  to the given location on the
        filesystem for persistent storage.
        """
        with open(loc, "w") as fh:
            json.dump(vars(self), fh, cls=encoder)
