# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from league_history_collector.models.roster import Roster
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class TeamGameData(CamelCasedDataclass):
    """Contains data about a team's performance in a game."""

    # Manager lists to accomodate co-managers.
    points: float
    managers: List[str]
    roster: Roster


@dataclass
class Game(CamelCasedDataclass):
    """Contains data about a specific game in a week."""

    team_data: List[TeamGameData]
