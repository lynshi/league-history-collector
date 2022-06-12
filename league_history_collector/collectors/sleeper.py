"""Collector for Sleeper leagues."""

from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, ClassVar, Dict, List, Set, Tuple

from loguru import logger
import requests

from league_history_collector.collectors.base import ICollector
from league_history_collector.collectors.models import (
    FinalStanding,
    League,
    Manager,
    ManagerStanding,
    RegularSeasonStanding,
    Season,
)
from league_history_collector.models.record import Record
from league_history_collector.utils import CamelCasedDataclass


@dataclass
class SleeperConfiguration(CamelCasedDataclass):
    """Extends the Configuration class with fields specific for NFL Fantasy."""

    league_id: str
    players_file: str
    year: int


class SleeperCollector(ICollector):
    """Collector for fantasy football leagues on Sleeper."""

    _all_players_endpoint: ClassVar[str] = "https://api.sleeper.app/v1/players/nfl"
    _managers_endpoint: ClassVar[str] = "https://api.sleeper.app/v1/league/{}/users"
    _matchups_endpoint: ClassVar[str] = "https://api.sleeper.app/v1/league/{}/matchups/{}"
    _playoffs_endpoint: ClassVar[
        str
    ] = "https://api.sleeper.app/v1/league/{}/winners_bracket"
    _rosters_endpoint: ClassVar[str] = "https://api.sleeper.app/v1/league/{}/rosters"

    def __init__(self, config: SleeperConfiguration):
        super().__init__()

        self._config = config
        self._players = self._update_players()

    def get_seasons(self) -> List[int]:
        raise NotImplementedError(
            "Not implemented for Sleeper, as league ids uniquely identify a season"
        )

    def save_all_data(self) -> League:
        league = League(self._config.league_id, managers={}, seasons={})
        self.set_season_data(self._config.year, league)
        return league

    def set_season_data(self, year: int, league: League):
        # Get mapping of team ID to manager ID, and list of managers for the year.
        team_to_manager, managers = self._get_managers()

        # Set up empty object.
        league.seasons[year] = Season(standings={}, weeks={})

        # Collect standings information.
        final_standings = self._get_final_standings(team_to_manager)
        regular_season_standings = self._get_regular_season_standings(team_to_manager)

        # Populate league with standings information.
        for manager_id, manager in managers.items():
            if manager_id not in league.managers:
                logger.debug(f"Adding manager {manager} to league")
                league.managers[manager_id] = manager
            else:
                league.managers[manager_id].seasons.append(year)

            manager_standing = ManagerStanding(
                final_standing=final_standings[manager_id],
                regular_season_standing=regular_season_standings[manager_id],
            )
            league.seasons[year].standings[manager_id] = manager_standing

        # Get and populate games information.
        weeks_in_league = self._get_weeks()
        for week in weeks_in_league:
            week_data = self._get_games_for_week(year, week, team_to_manager)
            league.seasons[year].weeks[week] = week_data

    def _update_players(self) -> Dict[str, Any]:
        existing_players = {}
        if os.path.isfile(self._config.players_file):
            with open(self._config.players_file, encoding="utf-8") as infile:
                existing_players = json.load(infile)

        if existing_players:
            # Per API docs, the players API only needs to be called once per day.
            last_updated = datetime.fromisoformat(existing_players["lastUpdated"])
            if datetime.now(tz=timezone.utc) - last_updated < timedelta(hours=24):
                return existing_players

        players = SleeperCollector._get_players()
        players["lastUpdated"] = datetime.now(tz=timezone.utc).isoformat()
        with open(self._config.players_file, "w", encoding="utf-8") as outfile:
            json.dump(players, outfile, indent=2, sort_keys=True)

        return players

    def _get_final_standings(
        self, team_to_manager: Dict[str, List[str]]
    ) -> Dict[str, FinalStanding]:
        # We don't actually care about the final standings, only the winner and runner-up, as nobody
        # takes the other matchups seriously. So since Sleeper doesn't make it easy to get the final
        # standings, we'll only set the winner and runner-up because that's the easier to do.
        playoffs_uri = SleeperCollector._playoffs_endpoint.format(
            self._config.league_id
        )
        logger.info(
            f"Getting final standings for {self._config.year} from {playoffs_uri}"
        )

        response = requests.get(playoffs_uri)
        response.raise_for_status()
        playoffs_data: List[Dict[Any, Any]] = response.json()

        # The runner-up is the team that loses to the champion.
        # The champion is the winner of the championship matchup.
        # The championship matchup is the matchup in the last round made up only of winners of
        # "valid" matchups.
        # "Valid" matchups are those in which participants are only winners of previous matchups.
        valid_matchups = set()

        # Sort the matchups in order of rounds, just in case they aren't ordered coming in.
        playoffs_data.sort(key=lambda m: (m["r"]))
        championship_round = None
        for matchup in playoffs_data:
            round_id = matchup["r"]
            championship_round = max(round_id, championship_round)
            if round_id == 1:
                valid_matchups.add((round_id, matchup["m"]))
                continue

            t1_from = matchup.get("t1_from", None)
            if t1_from:
                w = t1_from.get("w", None)
                if w is None or w not in valid_matchups:
                    continue

            t2_from = matchup.get("t2_from", None)
            if t2_from:
                w = t2_from.get("w", None)
                if w is None or w not in valid_matchups:
                    continue

            valid_matchups.add((round_id, matchup["m"]))

        logger.debug(
            f"The championship round in {self._config.year} is round {championship_round}"
        )

        # Separately set the championship matchup to ensure it is only set once.
        championship_matchup = None
        for r_id, m_id in valid_matchups:
            if r_id != championship_round:
                continue

            if championship_matchup is not None:
                raise ValueError(
                    f"The championship matchup was already to {championship_matchup}"
                )

            championship_matchup = m_id

        logger.debug(
            f"The championship matchup in {self._config.year} is round {championship_matchup}"
        )

        final_standings = {}
        # Start at the end because the championship round should be towards the end of the list.
        for i in range(len(playoffs_data) - 1, -1, -1):
            matchup = playoffs_data[i]
            if (
                matchup["r"] != championship_round
                or matchup["m"] != championship_matchup
            ):
                continue

            final_standings[team_to_manager[matchup["w"]]] = FinalStanding(1)
            final_standings[team_to_manager[matchup["l"]]] = FinalStanding(2)
            break

        assert (
            len(final_standings) == 2
        ), f"Expected two managers in final standings, got {final_standings}"
        logger.debug(f"Final standings in {self._config.year}: {final_standings}")
        return final_standings

    def _get_managers(self) -> Tuple[Dict[str, List[str]], Dict[str, Manager]]:
        managers_uri = SleeperCollector._managers_endpoint.format(
            self._config.league_id
        )
        logger.info(f"Getting managers for {self._config.year} from {managers_uri}")

        response = requests.get(managers_uri)
        response.raise_for_status()
        managers_data = response.json()

        managers_result = {}
        for manager in managers_data:
            managers_result[manager["user_id"]] = Manager(
                manager["username"], seasons=[self._config.year]
            )

        rosters_uri = SleeperCollector._rosters_endpoint.format(self._config.league_id)
        response = requests.get(rosters_uri)
        response.raise_for_status()
        rosters_data = response.json()

        team_to_manager = {}
        for roster in rosters_data:
            team_to_manager[roster["roster_id"]] = roster["owner_id"]
            logger.debug(
                f"In {self._config.year}, found manager {managers_result['owner_id'].name} for "
                f"team {roster['roster_id']}"
            )

        logger.debug(f"Team to manager mapping: {team_to_manager}")
        return team_to_manager, managers_result

    def _get_regular_season_standings(
        self, team_to_manager: Dict[str, List[str]]
    ) -> Dict[str, RegularSeasonStanding]:
        rosters_uri = SleeperCollector._rosters_endpoint.format(self._config.league_id)
        logger.info(
            f"Getting regular season standings for {self._config.year} from {rosters_uri}"
        )

        response = requests.get(rosters_uri)
        response.raise_for_status()
        rosters_data = response.json()

        # Sleeper doesn't have a nice API for getting the final standings, so we'll compute the
        # standings using an ordering that makes sense.
        teams = []
        TeamResults = namedtuple(
            "TeamResults",
            [
                "wins",
                "ties",
                "losses",
                "points_for",
                "points_against",
                "roster_id",
            ],
        )
        for roster in rosters_data:
            team_result = TeamResults(
                wins=roster["settings"]["wins"],
                ties=roster["settings"]["ties"],
                losses=roster["settings"]["losses"],
                points_for=float(
                    f'{roster["settings"]["fpts"]}.{roster["settings"]["fpts_decimal"]}'
                ),
                points_against=float(
                    f'{roster["settings"]["fpts_against"]}."'
                    f'{roster["settings"]["fpts_against_decimal"]}'
                ),
                roster_id=roster["roster_id"],
            )
            teams.append(team_result)
        teams.sort(
            key=lambda t: (t.wins, t.ties, t.points_for, t.points_against), reverse=True
        )

        regular_season_standings = {
            team[team_to_manager[team.roster_id]]: RegularSeasonStanding(
                rank=i + 1,
                points_scored=team.points_for,
                points_against=team.points_against,
                record=Record(
                    wins=team.wins,
                    ties=team.ties,
                    losses=team.losses,
                ),
            )
            for i, team in enumerate(teams)
        }

        for manager_id, standing in regular_season_standings.items():
            logger.debug(
                f"Regular season standing for manager {manager_id} in {self._config.year}: "
                f"{standing.to_json()}"
            )

        return regular_season_standings

    def _get_weeks(self) -> Set[int]:
        weeks = set()

        # The number of weeks may vary as the length of the NFL season has changed.
        # We'll exclude weeks without games. Since there might be a week with no games if we decide
        # to introduce bye weeks (...?), let's just count until a large number.
        for week_id in range(1, 32):
            week_uri = SleeperCollector._matchups_endpoint.format(self._config.league_id, week_id)
            logger.info(f"Checking if there are any games in week {week_id} at {week_uri}")

            response = requests.get(week_uri)
            response.raise_for_status()
            week_data = response.json()

            if week_data:
                weeks.add(week_id)

        logger.debug(f"Weeks with games: {weeks}")
        return weeks

    @staticmethod
    def _get_players() -> Dict[str, Any]:
        response = requests.get(SleeperCollector._all_players_endpoint)
        response.raise_for_status()
        return response.json()