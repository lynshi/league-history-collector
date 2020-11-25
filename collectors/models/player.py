# pylint: disable=missing-module-docstring

from dataclasses import dataclass

from collectors.models.base import CamelCasedDataclass


@dataclass
class Player(CamelCasedDataclass):
    """Contains data for a player."""

    id: str
    name: str
    position: str
