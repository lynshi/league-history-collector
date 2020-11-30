# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict

from league_history_collector.models import Record
from league_history_collector.collectors.models.week import Week
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class FinalStanding(CamelCasedDataclass):
    """Contains details about the final standing."""

    rank: int


@dataclass
class RegularSeasonStanding(CamelCasedDataclass):
    """Contains details about the regular season standing."""

    rank: int

    points_scored: float
    points_against: float

    record: Record


@dataclass
class ManagerStanding(CamelCasedDataclass):
    """Contains data for a manager's season."""

    final_standing: FinalStanding
    regular_season_standing: RegularSeasonStanding


@dataclass
class Season(CamelCasedDataclass):
    """Contains data about a season."""

    standings: Dict[str, ManagerStanding]
    weeks: Dict[int, Week]
