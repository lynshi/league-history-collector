# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from collectors.models.roster import Roster
from utils import CamelCasedDataclass


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
    winning_managers: List[str]
    tied: bool = False


@dataclass
class Week(CamelCasedDataclass):
    """Contains data for a single week."""

    games: List[Game]
