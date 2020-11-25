# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from collectors.models.base import CamelCasedDataclass
from collectors.models.record import Record
from collectors.models.roster import Roster


@dataclass
class Week(CamelCasedDataclass):
    """Contains data for a single week."""

    id: int  # e.g. 3 for Week 3

    opponent_id: List[
        str
    ]  # at least the opposing team's manager's ID, more if co-owned
    points_scored: float
    points_against: float

    breakdown: Record
    roster: Roster = Roster()
