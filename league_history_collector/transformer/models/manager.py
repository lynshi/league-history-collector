# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict

from league_history_collector.models import Record
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class ManagerSeason(
    CamelCasedDataclass
):  # pylint: disable=too-many-instance-attributes
    """Contains a manager's season data."""

    final_standing: int
    made_playoffs: bool
    playoff_games: Dict[int, int]  # Index into the week of the game
    playoff_record: Record

    consolation_games: Dict[int, int]

    regular_season_games: Dict[int, int]
    regular_season_points_against: float
    regular_season_points_scored: float
    regular_season_record: Record
    regular_season_standing: int


@dataclass
class Manager(CamelCasedDataclass):
    """Contains a manager's cumulative statistics."""

    seasons: Dict[int, ManagerSeason]


@dataclass
class Managers(CamelCasedDataclass):
    """Contains stats for all managers in the history of the league."""

    managers: Dict[str, Manager]
