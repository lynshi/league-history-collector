# pylint: disable=missing-module-docstring

from dataclasses import dataclass

from utils import CamelCasedDataclass


@dataclass
class Record(CamelCasedDataclass):
    """Represents a record."""

    wins: int
    losses: int
    ties: int
