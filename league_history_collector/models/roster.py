# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from league_history_collector.models.player import Player
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Roster(CamelCasedDataclass):
    """Contains data for a roster."""

    # Using Player objects will duplicate ID, name, and position, but this
    # helps account for position changes between seasons.

    starters: List[Player]
    bench: List[Player]
