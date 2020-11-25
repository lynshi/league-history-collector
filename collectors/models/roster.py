# pylint: disable=missing-module-docstring

from dataclasses import dataclass, field
from typing import List

from collectors.models.base import CamelCasedDataclass
from collectors.models.player import Player


@dataclass
class Roster(CamelCasedDataclass):
    """Contains data for a roster."""

    starters: List[Player] = field(default_factory=list)
    bench: List[Player] = field(default_factory=list)
