# pylint: disable=missing-module-docstring

from dataclasses import dataclass

from collectors.models.base import CamelCasedDataclass


@dataclass
class Manager(CamelCasedDataclass):
    """Contains a manager's data."""
