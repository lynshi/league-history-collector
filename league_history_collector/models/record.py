# pylint: disable=missing-module-docstring

from dataclasses import dataclass

from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Record(CamelCasedDataclass):
    """Represents a record, which is wins-losses-ties."""

    wins: int
    losses: int
    ties: int
