# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from collectors.models.player import Player
from utils import CamelCasedDataclass


@dataclass
class Roster(CamelCasedDataclass):
    """Contains data for a roster."""

    starters: List[Player]
    bench: List[Player]
