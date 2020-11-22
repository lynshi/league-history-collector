"""Defines module exports and interfaces."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import Optional
from dataclasses_json import dataclass_json, LetterCase


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Configuration:
    """Configuration data for a Collector."""

    username: str
    password: str

    @staticmethod
    def load(
        filename: Optional[str] = None, dict_config: Optional[dict] = None
    ) -> Configuration:
        """Builds a Configuration object from JSON data.

        Exactly one argument must not be None. The source of the JSON data may
        be configured with the arguments; for example, `filename` dictates the JSON be
        read from the specified filename."""

        args = [filename, dict_config]
        num_not_none = len(args) - args.count(None)
        if num_not_none != 1:
            raise ValueError(
                f"{num_not_none} arguments were not None, expected exactly 1 non-None"
            )

        if filename is not None:
            with open(filename) as infile:
                dict_config = json.load(infile)

        # pylint/pyright don't seem to understand that the following function comes from the
        # annotation. It doesn't seem like their comments can be combined.

        # pylint: disable=no-member
        return Configuration.from_dict(dict_config)  # type: ignore


class Collector(ABC):  # pylint: disable=too-few-public-methods
    """Abstract base class for collecting data."""

    def __init__(self, config: Configuration):  # pragma: no cover
        self._config = config

    @abstractmethod
    def save_all_data(self):
        """Save all retrievable data as desired by the implementation."""
