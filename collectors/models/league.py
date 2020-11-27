# pylint: disable=missing-module-docstring

from dataclasses import dataclass, field
from typing import Dict, NamedTuple, Optional

from dataclasses_json import Exclude
from dataclasses_json import config as dataclasses_json_config

from collectors.models.base import CamelCasedDataclass
from collectors.models.manager import Manager


class ManagerData(NamedTuple):
    """Combination of data to uniquely represent a manager. This helps differentiate
    managers with the same values for some attributes, such as the same name or co-managers."""

    name: str
    season: Optional[int] = None
    league_team_id: Optional[int] = None  # ID assigned by the hosting site


@dataclass
class League(CamelCasedDataclass):
    """Contains a league's data.

    If manager data clashes or inconsistencies are known ahead of time,
    the `manager_data_to_id` field should be initialized correctly. For example,
    if Alice manages team 1 in 2017 and team 2 in 2018, this information should
    be passed via this field."""

    id: str
    managers: Dict[str, Manager] = field(default_factory=dict)

    # Typing on the `exclude` parameter is inaccurate.
    manager_data_to_id: Dict[ManagerData, str] = field(
        metadata=dataclasses_json_config(exclude=Exclude.ALWAYS),  # type: ignore
        default_factory=dict,
    )

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
