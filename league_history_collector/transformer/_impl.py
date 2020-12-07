# pylint: disable=missing-module-docstring

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import league_history_collector.transformer.models as transformer_models
from league_history_collector.collectors.models import League, Manager
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Configuration(CamelCasedDataclass):
    """Configuration data for a Transformer."""

    # Specify the number of playoff teams. This will determine
    # teams inferred to be in the playoffs for each season.
    num_playoff_teams: int

    # Specify the number of playoff teams per season. This will determine
    # teams inferred to be in the playoffs for each season and override
    # `num_playoff_teams` if a value is present for a particular season.
    num_playoff_teams_by_season: Dict[int, int] = field(default_factory=dict)

    # Explicitly list the teams in the playoffs if the league has
    # some unique configuration beyond top N make playoffs. If this
    # field is available for a season, all other fields that related
    # to teams in the playoffs are ignored.
    playoff_teams: Dict[int, List[str]] = field(default_factory=dict)

    def is_in_playoffs(self, manager_id: str, *, rank: int, season: int) -> bool:
        """Returns whether the manager made the playoffs for the
        specified season."""

        playoff_teams = self.playoff_teams.get(season, [])
        if manager_id in playoff_teams:
            return True

        if len(playoff_teams) > 0:
            return False

        num_playoff_teams = self.num_playoff_teams_by_season.get(
            season, self.num_playoff_teams
        )

        return rank <= num_playoff_teams


class Transformer:
    """Transforms an input data model into multiple other models. By default,
    manager names are used to uniquely identify managers found in the input model.

    If `anonymizer` is provided, league manager names will be fed through the provided
    function to anonymize names. If `manager_id_mapping` is provided, it will be used instead
    to map manager ids to returned identifiers (e.g. team names)."""

    def __init__(
        self,
        config: Configuration,
        league_data: League,
        anonymizer: Optional[Callable[[str], str]] = None,
        manager_id_mapping: Optional[Callable[[str], str]] = None,
    ):
        if anonymizer is not None and manager_id_mapping is not None:
            raise ValueError(
                "`anonymizer` and `manager_id_mapping` cannot both be provided"
            )

        self._config = config
        self._data = deepcopy(league_data)

        seen_names = {}
        if anonymizer is not None:
            anonymized = {}
            for manager_id, manager in self._data.managers.items():
                new_name = anonymizer(manager.name)
                if new_name in seen_names:
                    raise RuntimeError(
                        f"At least two managers [{seen_names[new_name]}, {manager_id}] "
                        f"have the same name: {new_name}"
                    )

                seen_names[new_name] = manager_id

                anonymized[manager_id] = Manager(new_name, manager.seasons)

            self._data.managers = anonymized
        elif manager_id_mapping is not None:
            mapped = {}
            for manager_id, manager in self._data.managers.items():
                new_name = manager_id_mapping(manager_id)
                if new_name in seen_names:
                    raise RuntimeError(
                        f"At least two managers [{seen_names[new_name]}, {manager_id}] "
                        f"have the same name: {new_name}"
                    )

                seen_names[new_name] = manager_id

                mapped[manager_id] = Manager(new_name, manager.seasons)

            self._data.managers = mapped
        else:
            for manager_id, manager in self._data.managers.items():
                name = manager.name
                if name in seen_names:
                    raise RuntimeError(
                        f"At least two managers [{seen_names[name]}, {manager_id}] "
                        f"have the same name: {name}"
                    )

                seen_names[name] = manager_id

        self._league_summary = None
        self._games = None
        self._head_to_head = None
        self._seasons = None
        self._managers = None

    @property
    def league_summary(self) -> transformer_models.LeagueSummary:
        """Returns a model for the league summary, raising an exception if it has
        not been computed yet."""

        if self._league_summary is None:
            raise RuntimeError("League summary has not been computed yet")

        return self._league_summary

    @property
    def games(self) -> transformer_models.Games:
        """Returns a model for the games, raising an exception if it has
        not been computed yet."""

        if self._games is None:
            raise RuntimeError("Games has not been computed yet")

        return self._games

    @property
    def head_to_head(self) -> transformer_models.HeadToHead:
        """Returns a model for the head to head results, raising an exception if it has
        not been computed yet."""

        if self._head_to_head is None:
            raise RuntimeError("Head to head results have not been computed yet")

        return self._head_to_head

    @property
    def seasons(self) -> transformer_models.Seasons:
        """Returns a model for the seasons, raising an exception if it has
        not been computed yet."""

        if self._seasons is None:
            raise RuntimeError("Seasons not been computed yet")

        return self._seasons

    @property
    def managers(self) -> transformer_models.Managers:
        """Returns a model for the managers, raising an exception if it has
        not been computed yet."""

        if self._managers is None:
            raise RuntimeError("Managers has not been computed yet")

        return self._managers

    def transform(self):
        """Transforms input data into new, internally-stored models that can
        be retrieved by associated properties."""

        assert self._games is None
