# pylint: disable=missing-module-docstring

from dataclasses import dataclass

from collectors.models.base import CamelCasedDataclass


@dataclass
class Record(CamelCasedDataclass):
    """Encapsulates a record, which is wins-losses-ties."""

    wins: int = 0
    losses: int = 0
    ties: int = 0
