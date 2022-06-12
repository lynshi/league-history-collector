"""Base interfaces for collectors."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import List, Optional

from league_history_collector.collectors.models import League
from league_history_collector.utils import CamelCasedDataclass


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

    @abstractmethod
    def set_season_data(self, year: int, league: League):
        """Sets data for the specified season in the provided league object.

        :param year: Year of the season.
        :type year: int
        :param league: League data object, to be modified by this method.
        :type league: League
        """

    @abstractmethod
    def get_seasons(self) -> List[int]:
        """Gets a list of seasons in the league.

        :return: A list of seasons, identified by year.
        :rtype: List[int]
        """
