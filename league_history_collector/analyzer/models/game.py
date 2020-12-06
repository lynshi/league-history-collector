# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict

from league_history_collector.models import Game
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Games(CamelCasedDataclass):
    """Collection of all the games in the league's history."""

    games: Dict[int, Dict[int, Game]]
