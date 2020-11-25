# pylint: disable=missing-module-docstring

from dataclasses import dataclass, field
from typing import Dict

from collectors.models.base import CamelCasedDataclass
from collectors.models.record import Record
from collectors.models.week import Week


@dataclass
class Season(CamelCasedDataclass):  # pylint: disable=too-many-instance-attributes
    """Contains data for a manager's season."""

    id: int  # e.g. a year

    final_rank: int

    regular_season_rank: int
    regular_season_points_scored: float
    regular_season_points_against: float

    regular_season_record: Record
    regular_season_breakdown: Record

    weeks: Dict[int, Week] = field(default_factory=dict)
