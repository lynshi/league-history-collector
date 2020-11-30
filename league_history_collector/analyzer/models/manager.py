# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict

from league_history_collector.models import Game, Record
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class ManagerSeason(
    CamelCasedDataclass
):  # pylint: disable=too-many-instance-attributes
    """Contains a manager's season data."""

    final_standing: int
    consolation_games: Dict[int, Game]
    playoff_games: Dict[int, Game]

    made_playoffs: bool
    regular_season_games: Dict[int, Game]
    regular_season_points_against: float
    regular_season_points_scored: float
    regular_season_record: Record
    regular_season_standing: int


@dataclass
class Manager(CamelCasedDataclass):
    """Contains a manager's cumulative statistics."""

    seasons: Dict[int, ManagerSeason]
