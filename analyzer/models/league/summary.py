# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict

from analyzer.models.record import Record
from utils import CamelCasedDataclass


@dataclass
class LeagueSummary(CamelCasedDataclass):  # pylint: disable=too-many-instance-attributes
    """League data totals."""

    # Playoff stats
    average_final_standing: Dict[str, float]
    champions: Dict[int, str]
    total_playoff_record: Dict[str, Record]

    # Regular season stats
    average_regular_season_standing: Dict[str, float]
    seasons_played: Dict[str, int]
    total_playoff_appearances: Dict[str, int]
    total_regular_season_record: Dict[str, Record]
    total_regular_season_points_scored: Dict[str, float]
