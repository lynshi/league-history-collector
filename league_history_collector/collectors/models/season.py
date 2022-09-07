# pylint: disable=missing-module-docstring

from dataclasses import dataclass, field
from typing import Dict, Optional

from dataclasses_json.cfg import config

from league_history_collector.models import Record
from league_history_collector.collectors.models.draft import Draft
from league_history_collector.collectors.models.week import Week
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class FinalStanding(CamelCasedDataclass):
    """Contains details about the final standing."""

    rank: Optional[int]


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

    # Platforms like Sleeper have a different league id per season.
    league_id: Optional[int] = field(
        default=None, metadata=config(exclude=lambda val: val is None)  # type: ignore
    )
    draft_results: Optional[Draft] = field(
        default=None, metadata=config(exclude=lambda val: val is None)  # type: ignore
    )
