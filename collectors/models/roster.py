# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from utils import CamelCasedDataclass


@dataclass
class Player(CamelCasedDataclass):
    """Contains data for a player."""

    id: str
    name: str
    position: str


@dataclass
class Roster(CamelCasedDataclass):
    """Contains data for a roster."""

    starters: List[Player]
    bench: List[Player]
