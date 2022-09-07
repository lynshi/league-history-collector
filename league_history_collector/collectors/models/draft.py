# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from league_history_collector.utils import CamelCasedDataclass


@dataclass
class DraftPick(CamelCasedDataclass):
    """Contains information about a draft pick."""

    round: int
    round_slot: int
    overall_pick: int
    player_id: str
    player_position: str
    manager_id: str


@dataclass
class Draft(CamelCasedDataclass):
    """Contains information about a draft."""

    drafts: List[List[DraftPick]]
