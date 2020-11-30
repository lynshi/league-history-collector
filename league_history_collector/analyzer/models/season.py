# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict, List

from league_history_collector.models import Game
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Season(CamelCasedDataclass):
    """Stores statistics about a season."""

    champion: str
    final_standings: Dict[str, int]
    playoff_games: Dict[int, Game]

    playoff_teams = List[str]
    regular_season_standings: Dict[str, int]
    regular_season_points_for: Dict[str, float]
    regular_season_points_again: Dict[str, float]
