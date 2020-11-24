# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import List

from collectors.models.base import CamelCasedDataclass
from collectors.models.manager import Manager


@dataclass
class League(CamelCasedDataclass):
    """Contains a league's data."""

    id: str  # pylint: disable=invalid-name
    managers: List[Manager]
