# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Manager(CamelCasedDataclass):
    """Contains a manager's data."""

    name: str
    seasons: List[int]  # List of years
