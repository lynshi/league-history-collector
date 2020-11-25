# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from collectors.models.base import CamelCasedDataclass
from collectors.models.player import Player


@dataclass
class Roster(CamelCasedDataclass):
    """Contains data for a roster."""

    starters: List[Player] = []
    bench: List[Player] = []
