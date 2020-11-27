# pylint: disable=missing-module-docstring

from dataclasses import dataclass, field
from typing import Dict

from collectors.models.base import CamelCasedDataclass
from collectors.models.manager import Manager


@dataclass
class League(CamelCasedDataclass):
    """Contains a league's data.

    If manager data clashes or inconsistencies are known ahead of time,
    the `manager_data_to_id` field should be initialized correctly. For example,
    if Alice manages team 1 in 2017 and team 2 in 2018, this information should
    be passed via this field."""

    id: str
    managers: Dict[str, Manager] = field(default_factory=dict)
