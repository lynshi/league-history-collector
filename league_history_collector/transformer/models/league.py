# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict

from league_history_collector.models import Record
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class LeagueSummary(
    CamelCasedDataclass
):  # pylint: disable=too-many-instance-attributes
    """League data totals."""

    # Regular season stats
    regular_season_standings: Dict[str, Dict[int, int]]
    seasons_played: Dict[str, int]
    total_regular_season_points_scored: Dict[str, float]
    total_regular_season_record: Dict[str, Record]

    # Playoff stats
    champions: Dict[int, str]
    final_standings: Dict[str, Dict[int, int]]
    total_playoff_appearances: Dict[str, int]
    total_playoff_points_scored: Dict[str, float]
    total_playoff_record: Dict[str, Record]
