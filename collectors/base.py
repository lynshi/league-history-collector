"""Base interfaces for collectors."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
from typing import Dict, NamedTuple, Optional

from collectors.models import CamelCasedDataclass, League


@dataclass
class Configuration(CamelCasedDataclass):
    """Configuration data for a Collector."""

    username: str
    password: str

    @staticmethod
    def load(
        filename: Optional[str] = None, dict_config: Optional[dict] = None
    ) -> Configuration:
        """Build a Configuration object from JSON data.

        Exactly one argument must not be None. The source of the JSON data may
        be configured with the arguments; for example, `filename` dictates the JSON be
        read from the specified filename."""

        dict_config = Configuration._get_dict_config(
            filename=filename, dict_config=dict_config
        )

        return Configuration.from_dict(dict_config)

    @staticmethod
    def _get_dict_config(
        filename: Optional[str] = None, dict_config: Optional[dict] = None
    ) -> dict:
        args = [filename, dict_config]
        num_not_none = len(args) - args.count(None)
        if num_not_none != 1:
            raise ValueError(
                f"{num_not_none} arguments were not None, expected exactly 1 non-None"
            )

        if filename is not None:
            with open(filename) as infile:
                dict_config = json.load(infile)

        assert dict_config is not None  # pacify static type checker
        return dict_config


class ICollector(ABC):  # pylint: disable=too-few-public-methods
    """Abstract base class for collecting data."""

    @abstractmethod
    def save_all_data(self) -> League:
        """Save all retrievable data as desired by the implementation."""


class ManagerData(NamedTuple):
    """Combination of data to uniquely represent a manager. This helps differentiate
    managers with the same values for some attributes, such as the same name or co-managers."""

    name: str
    season: Optional[int] = None
    league_team_id: Optional[int] = None  # ID assigned by the hosting site


class ManagerIdRetriever:  # pylint: disable=too-few-public-methods
    """Helper class for retrieving the manager ID from configuration."""

    def __init__(self, manager_data_to_id: Optional[Dict[ManagerData, str]] = None):
        self.manager_data_to_id = (
            manager_data_to_id if manager_data_to_id is not None else {}
        )

    # Typing on the `exclude` parameter is inaccurate.
    manager_data_to_id: Dict[ManagerData, str] = field(default_factory=dict)

    def get_manager_id(self, manager_data: ManagerData) -> str:
        """Returns a manager's ID given uniquely-identifying data.

        If no pre-assigned ID is found, the returned ID is just the manager's name.
        If multiple managers have the same name, the expectation is for the creator
        of this object to dictate the assigned ID via `manager_data_to_id`."""

        manager_id = self.manager_data_to_id.get(manager_data, None)
        if manager_id is not None:
            return manager_id

        manager_id = f"{manager_data.name}"

        self.manager_data_to_id[manager_data] = manager_id
        return manager_id
