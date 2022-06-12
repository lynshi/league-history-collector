"""Collector for Sleeper leagues."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, ClassVar, Dict, List, Tuple

from loguru import logger
import requests

from league_history_collector.collectors.base import ICollector
from league_history_collector.collectors.models import (
    FinalStanding,
    League,
    Manager,
    Season,
)
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
        regular_season_standings = self._get_regular_season_standings(
            year, team_to_manager
        )

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
        weeks_in_league = self._get_weeks(year)
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

    def _get_managers(self) -> Tuple[Dict[str, List[str]], Dict[str, Manager]]:
        managers_uri = SleeperCollector._managers_endpoint.format(
            self._config.league_id
        )
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

        return team_to_manager, managers_result

    def _get_regular_season_standings(
        self, team_to_manager: Dict[str, List[str]]
    ) -> Dict[str, FinalStanding]:
        rosters_uri = SleeperCollector._rosters_endpoint.format(self._config.league_id)
        response = requests.get(rosters_uri)
        response.raise_for_status()
        rosters_data = response.json()

        # Sleeper doesn't have a nice API for getting the final standings, so we'll compute the
        # standings using an ordering that makes sense.
        teams = []
        for roster in rosters_data:
            teams.append(
                (
                    roster["settings"]["wins"],
                    roster["settings"]["ties"],
                    roster["settings"]["fpts"],
                    roster["settings"]["fpts_decimal"],
                    roster["settings"]["fpts_against"],
                    roster["settings"]["fpts_against_decimal"],
                    team_to_manager["roster_id"],
                )
            )
        teams.sort(reverse=True)

        final_standings = {
            team[-1]: FinalStanding(i + 1) for i, team in enumerate(teams)
        }
        return final_standings

    @staticmethod
    def _get_players() -> Dict[str, Any]:
        response = requests.get(SleeperCollector._all_players_endpoint)
        response.raise_for_status()
        return response.json()
