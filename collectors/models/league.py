# pylint: disable=missing-module-docstring

from dataclasses import dataclass


@dataclass
class League:
    """Contains a league's data."""

    _id: int
