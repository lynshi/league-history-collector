# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict, List

from league_history_collector.models import Record
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Season(CamelCasedDataclass):  # pylint: disable=too-many-instance-attributes
    """Stores statistics about a season."""

    regular_season_standings: Dict[str, int]
    regular_season_records: Dict[str, Record]
    regular_season_points_for: Dict[str, float]
    regular_season_points_against: Dict[str, float]

    playoff_teams = List[str]
    final_standings: Dict[str, int]


@dataclass
class Seasons(CamelCasedDataclass):
    """Stores statistics for all seasons."""

    seasons: Dict[int, Season]
