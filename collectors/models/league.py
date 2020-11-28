# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict

from collectors.models.manager import Manager
from collectors.models.season import Season
from utils import CamelCasedDataclass


@dataclass
class League(CamelCasedDataclass):
    """Contains a league's data."""

    id: str
    managers: Dict[str, Manager]
    seasons: Dict[int, Season]
