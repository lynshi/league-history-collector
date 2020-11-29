# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict

from league_history_collector.collectors.models.manager import Manager
from league_history_collector.collectors.models.season import Season
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class League(CamelCasedDataclass):
    """Contains a league's data."""

    id: str
    managers: Dict[str, Manager]
    seasons: Dict[int, Season]
