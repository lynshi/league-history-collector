# pylint: disable=missing-module-docstring

from dataclasses import dataclass, field
from typing import Dict

from collectors.models.base import CamelCasedDataclass
from collectors.models.season import Season


@dataclass
class Manager(CamelCasedDataclass):
    """Contains a manager's data."""

    id: str
    seasons: Dict[str, Season] = field(default_factory=dict)
