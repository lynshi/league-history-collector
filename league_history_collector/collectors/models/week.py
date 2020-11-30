# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from league_history_collector.models import Game
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Week(CamelCasedDataclass):
    """Contains data for a single week."""

    games: List[Game]
