# pylint: disable=missing-module-docstring

from dataclasses import dataclass
from typing import Dict, List, Tuple

from league_history_collector.utils import CamelCasedDataclass


@dataclass
class HeadToHead(CamelCasedDataclass):
    """Collection of head-to-head matchups."""

    # Manager -> Opponent -> [(Season, Week)]
    matchups: Dict[str, Dict[str, List[Tuple[int, int]]]]
