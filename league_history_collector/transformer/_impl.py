# pylint: disable=missing-module-docstring

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from loguru import logger

import league_history_collector.collectors.models as collector_models
import league_history_collector.models as shared_models
import league_history_collector.transformer.models as transformer_models
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class Configuration(CamelCasedDataclass):
    """Configuration data for a Transformer."""

    # Specify the number of playoff teams. This will determine
    # teams inferred to be in the playoffs for each season.
    num_playoff_teams: int

    # List of week numbers corresponding to playoffs.
    playoff_weeks: List[int]

    # Specify the number of playoff teams per season. This will determine
    # teams inferred to be in the playoffs for each season and override
    # `num_playoff_teams` if a value is present for a particular season.
    num_playoff_teams_by_season: Dict[int, int] = field(default_factory=dict)

    # Explicitly list the teams in the playoffs if the league has
    # some unique configuration beyond top N make playoffs. If this
    # field is available for a season, all other fields that related
    # to teams in the playoffs are ignored.
    playoff_teams: Dict[int, List[str]] = field(default_factory=dict)

    # Explicitly configure the list of week numbers for the playoffs for a particular season.
    # Overrides the playoff_weeks attribute when applicable.
    playoff_weeks_by_season: Dict[int, List[int]] = field(default_factory=dict)

    def is_in_playoffs(self, manager_name: str, *, rank: int, season: int) -> bool:
        """Returns whether the manager made the playoffs for the
        specified season."""

        playoff_teams = self.playoff_teams.get(season, [])
        if manager_name in playoff_teams:
            return True

        if len(playoff_teams) > 0:
            return False

        num_playoff_teams = self.num_playoff_teams_by_season.get(
            season, self.num_playoff_teams
        )

        return rank <= num_playoff_teams

    def playoff_weeks_for_season(self, year: int):
        """Returns the week numbers for playoff weeks for the specified season."""

        return self.playoff_weeks_by_season.get(year, self.playoff_weeks)


class Transformer:
    """Transforms an input data model into multiple other models. By default,
    manager names are used to uniquely identify managers found in the input model.

    If `anonymizer` is provided, league manager names will be fed through the provided
    function to anonymize names. If `manager_id_mapping` is provided, it will be used instead
    to map manager ids to returned identifiers (e.g. team names)."""

    def __init__(
        self,
        config: Configuration,
        league_data: collector_models.League,
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

                anonymized[manager_id] = collector_models.Manager(
                    new_name, manager.seasons
                )
                logger.debug(f"Renaming {(manager_id, manager.name)} to {new_name}")

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

                mapped[manager_id] = collector_models.Manager(new_name, manager.seasons)
                logger.debug(f"Renaming {(manager_id, manager.name)} to {new_name}")

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

        args = [{}] * 9
        self._league_summary = transformer_models.LeagueSummary(*args)
        self._games = transformer_models.Games({})
        self._head_to_head = transformer_models.HeadToHead({})
        self._seasons = transformer_models.Seasons({})
        self._managers = transformer_models.Managers({})

        self._transformed = False

    @property
    def league_summary(self) -> transformer_models.LeagueSummary:
        """Returns a model for the league summary, raising an exception if it has
        not been computed yet."""

        if self._transformed is False:
            raise RuntimeError(
                "League summary has not been computed yet, please call transform()."
            )

        return self._league_summary

    @property
    def games(self) -> transformer_models.Games:
        """Returns a model for the games, raising an exception if it has
        not been computed yet."""

        if self._transformed is False:
            raise RuntimeError(
                "Games has not been computed yet, please call transform()."
            )

        return self._games

    @property
    def head_to_head(self) -> transformer_models.HeadToHead:
        """Returns a model for the head to head results, raising an exception if it has
        not been computed yet."""

        if self._transformed is False:
            raise RuntimeError(
                "Head to head results have not been computed yet, please call transform()."
            )

        return self._head_to_head

    @property
    def seasons(self) -> transformer_models.Seasons:
        """Returns a model for the seasons, raising an exception if it has
        not been computed yet."""

        if self._transformed is False:
            raise RuntimeError(
                "Seasons not been computed yet, please call transform()."
            )

        return self._seasons

    @property
    def managers(self) -> transformer_models.Managers:
        """Returns a model for the managers, raising an exception if it has
        not been computed yet."""

        if self._transformed is False:
            raise RuntimeError(
                "Managers has not been computed yet, please call transform()."
            )

        return self._managers

    def transform(self):
        """Transforms input data into new, internally-stored models that can
        be retrieved by associated properties."""

        if self._transformed is True:
            logger.info(
                "transform has already been called so nothing will be done. Please use this object's properties to get transformed data."
            )
            return

        self._set_games_and_h2h()
        self._set_managers()

        self._transformed = True

    def _set_games_and_h2h(self):  # pylint: disable=too-many-locals
        head_to_head_result = {"matchups": {}}
        for _, manager in self._data.managers.items():
            head_to_head_result["matchups"][manager.name] = {}

        for manager_name in head_to_head_result["matchups"]:
            for mname in head_to_head_result["matchups"]:
                head_to_head_result["matchups"][manager_name][mname] = []

        games_result = {"games": {}}
        for year, season in self._data.seasons.items():
            self._populate_h2h_and_games_for_season(
                year,
                season,
                head_to_head_result=head_to_head_result,
                games_result=games_result,
            )

        self._games = transformer_models.Games.from_dict(games_result)
        self._head_to_head = transformer_models.HeadToHead.from_dict(
            head_to_head_result
        )

    def _get_name_for_manager_id(self, team_id: str) -> str:
        return self._data.managers[team_id].name

    def _populate_h2h_and_games_for_season(
        self,
        year: int,
        season: collector_models.Season,
        *,
        head_to_head_result: Dict,
        games_result: Dict,
    ):
        games_result["games"][year] = {}
        for week_num, week in season.weeks.items():
            for game in week.games:
                games_result["games"][year][week_num] = shared_models.Game(
                    team_data=[
                        shared_models.TeamGameData(
                            points=team_data.points,
                            managers=[
                                self._get_name_for_manager_id(team_id)
                                for team_id in team_data.managers
                            ],
                            roster=team_data.roster,
                        )
                        for team_data in game.team_data
                    ]
                )

                if len(game.team_data) != 2:
                    raise ValueError(
                        f"Amount of team data present is not two: {game.team_data}"
                    )

                first_team = game.team_data[0].managers
                second_team = game.team_data[1].managers

                for first_manager in first_team:
                    for second_manager in second_team:
                        head_to_head_result["matchups"][first_manager][
                            second_manager
                        ].append((year, week_num))
                        head_to_head_result["matchups"][second_manager][
                            first_manager
                        ].append((year, week_num))

    def _set_managers(self):
        managers_result = {"managers": {}}
        for _, manager in self._data.managers.items():
            managers_result["managers"][manager.name] = {"seasons": {}}
            for year in manager.seasons:
                managers_result["managers"][manager.name]["seasons"][year] = {}

        for year, season in self._data.seasons.items():
            self._populate_manager_results(
                year, season.standings, managers_result, self._games
            )

        self._managers = transformer_models.Managers.from_dict(managers_result)

    def _populate_manager_results(
        self,
        year: int,
        standings: Dict[str, collector_models.ManagerStanding],
        managers_result: Dict,
        games: transformer_models.Games,
    ):
        for mid, standing in standings.items():
            manager_name = self._get_name_for_manager_id(mid)
            made_playoffs = self._config.is_in_playoffs(
                manager_name, rank=standing.regular_season_standing.rank, season=year
            )
            playoff_weeks = self._config.playoff_weeks_for_season(year)

            managers_result["managers"][manager_name]["seasons"][year] = {
                "year": year,
                "madePlayoffs": made_playoffs,
                "playoffGames": playoff_weeks,
                "playoffRecord": shared_models.Record(),
            }

    def _compute_playoff_record(
        self,
        year: int,
        playoff_weeks: List[int],
        manager_name: str,
        games: transformer_models.Games,
    ) -> shared_models.Record:
        return shared_models.Record(0, 0, 0)


# year: int  # useful for pandas

#     final_standing: int
#     made_playoffs: bool
#     playoff_games: Dict[int, int]  # Index into the week of the game
#     playoff_record: Record

#     consolation_games: Dict[int, int]

#     regular_season_games: Dict[int, int]
#     regular_season_points_against: float
#     regular_season_points_scored: float
#     regular_season_record: Record
#     regular_season_standing: int
