# pylint: disable=too-many-locals,duplicate-code

"""Collector for Sleeper leagues."""

from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, ClassVar, Dict, List, Set, Tuple

from dataclasses_json.api import DataClassJsonMixin
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
    Week,
)
from league_history_collector.models import Game, Player, Record, Roster, TeamGameData


@dataclass
class SleeperConfiguration(DataClassJsonMixin):
    """Configuration for getting data from Sleeper."""

    league_id: str
    players_file: str


class SleeperCollector(ICollector):
    """Collector for fantasy football leagues on Sleeper."""

    _all_players_endpoint: ClassVar[str] = "https://api.sleeper.app/v1/players/nfl"
    _managers_endpoint: ClassVar[str] = "https://api.sleeper.app/v1/league/{}/users"
    _matchups_endpoint: ClassVar[
        str
    ] = "https://api.sleeper.app/v1/league/{}/matchups/{}"
    _league_endpoint: ClassVar[str] = "https://api.sleeper.app/v1/league/{}"
    _playoffs_endpoint: ClassVar[
        str
    ] = "https://api.sleeper.app/v1/league/{}/winners_bracket"
    _rosters_endpoint: ClassVar[str] = "https://api.sleeper.app/v1/league/{}/rosters"

    def __init__(self, config: SleeperConfiguration):
        super().__init__()

        self._config = config
        self._players = self._update_players()

        self._create_season_id_mappings()

    def _create_season_id_mappings(self) -> None:
        """Creates mappings between seasons and league ids as Sleeper creates a new league for each
        season.
        """
        self.season_to_id = {}
        self.id_to_season = {}

        next_league_id = self._config.league_id
        while next_league_id is not None:
            current_league_id = next_league_id
            endpoint = SleeperCollector._league_endpoint.format(current_league_id)
            response = requests.get(endpoint)
            response.raise_for_status()
            response_json = response.json()

            current_season = response_json["season"]
            self.season_to_id[current_season] = current_league_id
            self.id_to_season[current_league_id] = current_season

            next_league_id = response_json["previous_league_id"]

    def get_seasons(self) -> List[int]:
        return sorted(list(self.season_to_id.keys()), reverse=True)

    def save_all_data(self) -> League:
        league = League(self._config.league_id, managers={}, seasons={})
        seasons = self.get_seasons()
        for year in seasons:
            self.set_season_data(year, league)

        return league

    def set_season_data(self, year: int, league: League):
        # Get mapping of team ID to manager ID, and list of managers for the year.
        team_to_manager, managers = self._get_managers(year)

        # Set up empty object.
        league.seasons[year] = Season(
            standings={}, weeks={}, league_id=self.season_to_id[year]
        )

        # Collect standings information.
        final_standings = self._get_final_standings(year, team_to_manager)
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
                final_standing=final_standings.get(manager_id, FinalStanding(None)),
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

    def _get_final_standings(  # pylint: disable=too-many-locals,too-many-branches
        self,
        year: int,
        team_to_manager: Dict[str, List[str]],
    ) -> Dict[str, FinalStanding]:
        # We don't actually care about the final standings, only the winner and runner-up, as nobody
        # takes the other matchups seriously. So since Sleeper doesn't make it easy to get the final
        # standings, we'll only set the winner and runner-up because that's the easier to do.
        playoffs_uri = SleeperCollector._playoffs_endpoint.format(
            self.season_to_id[year]
        )
        logger.info(f"Getting final standings for {year} from {playoffs_uri}")

        response = requests.get(playoffs_uri)
        response.raise_for_status()
        playoffs_data: List[Dict[Any, Any]] = response.json()

        # The runner-up is the team that loses to the champion.
        # The champion is the winner of the championship matchup.
        # The championship matchup is the matchup in the last round made up only of winners of
        # "valid" matchups.
        # "Valid" matchups are those in which participants are only winners of previous matchups.
        valid_matchups = set()
        valid_matchups_including_round = set()

        # Sort the matchups in order of rounds, just in case they aren't ordered coming in.
        playoffs_data.sort(key=lambda m: (m["r"]))
        championship_round = None
        for matchup in playoffs_data:
            round_id = matchup["r"]
            championship_round = (
                max(round_id, championship_round)
                if championship_round is not None
                else round_id
            )
            if round_id == 1:
                valid_matchups.add(matchup["m"])
                valid_matchups_including_round.add((round_id, matchup["m"]))
                continue

            t1_from = matchup.get("t1_from", None)
            if t1_from:
                w = t1_from.get("w", None)  # pylint: disable=invalid-name
                if w is None or w not in valid_matchups:
                    continue

            t2_from = matchup.get("t2_from", None)
            if t2_from:
                w = t2_from.get("w", None)  # pylint: disable=invalid-name
                if w is None or w not in valid_matchups:
                    continue

            valid_matchups.add(matchup["m"])
            valid_matchups_including_round.add((round_id, matchup["m"]))

        logger.debug(f"The championship round in {year} is round {championship_round}")

        # Separately set the championship matchup to ensure it is only set once.
        championship_matchup = None
        for r_id, m_id in valid_matchups_including_round:
            if r_id != championship_round:
                continue

            if championship_matchup is not None:
                raise ValueError(
                    f"The championship matchup was already to {championship_matchup}"
                )

            championship_matchup = m_id

        logger.debug(
            f"The championship matchup in {year} is round {championship_matchup}"
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

            managers = team_to_manager[matchup["w"]]
            for manager_id in managers:
                final_standings[manager_id] = FinalStanding(1)

            managers = team_to_manager[matchup["l"]]
            for manager_id in managers:
                final_standings[manager_id] = FinalStanding(2)
            break

        assert (
            final_standings
        ), f"Expected final standings to be populated, got {final_standings}"
        logger.debug(f"Final standings in {year}: {final_standings}")
        return final_standings

    def _get_managers(
        self, year: int
    ) -> Tuple[Dict[str, List[str]], Dict[str, Manager]]:
        managers_uri = SleeperCollector._managers_endpoint.format(
            self.season_to_id[year]
        )
        logger.info(f"Getting managers for {year} from {managers_uri}")

        response = requests.get(managers_uri)
        response.raise_for_status()
        managers_data = response.json()

        managers_result = {}
        for manager in managers_data:
            managers_result[manager["user_id"]] = Manager(
                manager["display_name"], seasons=[year]
            )

        rosters_uri = SleeperCollector._rosters_endpoint.format(self.season_to_id[year])
        response = requests.get(rosters_uri)
        response.raise_for_status()
        rosters_data = response.json()

        team_to_manager = {}
        for roster in rosters_data:
            if roster["roster_id"] not in team_to_manager:
                team_to_manager[roster["roster_id"]] = []

            team_to_manager[roster["roster_id"]].append(roster["owner_id"])
            logger.debug(
                f"In {year}, found manager {managers_result[roster['owner_id']].name} "
                f"for team {roster['roster_id']}"
            )

        logger.debug(f"Team to manager mapping: {team_to_manager}")
        return team_to_manager, managers_result

    def _get_regular_season_standings(
        self,
        year: int,
        team_to_manager: Dict[str, List[str]],
    ) -> Dict[str, RegularSeasonStanding]:
        rosters_uri = SleeperCollector._rosters_endpoint.format(self.season_to_id[year])
        logger.info(f"Getting regular season standings for {year} from {rosters_uri}")

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
                    f'{roster["settings"]["fpts"]}.'
                    f'{str(roster["settings"]["fpts_decimal"]).zfill(2)}'
                ),
                points_against=float(
                    f'{roster["settings"]["fpts_against"]}.'
                    f'{str(roster["settings"]["fpts_against_decimal"]).zfill(2)}'
                ),
                roster_id=roster["roster_id"],
            )
            teams.append(team_result)
        teams.sort(
            key=lambda t: (t.wins, t.ties, t.points_for, t.points_against), reverse=True
        )

        regular_season_standings = {}
        for i, team in enumerate(teams):
            managers = team_to_manager[team.roster_id]
            for manager_id in managers:
                regular_season_standings[manager_id] = RegularSeasonStanding(
                    rank=i + 1,
                    points_scored=team.points_for,
                    points_against=team.points_against,
                    record=Record(
                        wins=team.wins,
                        ties=team.ties,
                        losses=team.losses,
                    ),
                )

        for manager_id, standing in regular_season_standings.items():
            logger.debug(
                f"Regular season standing for manager {manager_id} in {year}: "
                f"{standing.to_json()}"
            )

        return regular_season_standings

    def _get_weeks(self, year: int) -> Set[int]:
        weeks = set()

        # The number of weeks may vary as the length of the NFL season has changed.
        # We'll exclude weeks without games. Since there might be a week with no games if we decide
        # to introduce bye weeks (...?), let's just count until a large number.
        for week_id in range(1, 32):
            week_uri = SleeperCollector._matchups_endpoint.format(
                self.season_to_id[year], week_id
            )
            logger.info(
                f"Checking if there are any games in week {week_id} at {week_uri}"
            )

            response = requests.get(week_uri)
            response.raise_for_status()
            week_data = response.json()

            if week_data:
                weeks.add(week_id)
                logger.debug(f"Week {week_id} in season {year} has games")
            else:
                logger.debug(f"Week {week_id} in season {year} has no games")

        logger.debug(f"Weeks with games: {weeks}")
        return weeks

    def _get_games_for_week(  # pylint: disable=too-many-locals
        self, year: int, week: int, team_to_manager: Dict[str, List[str]]
    ) -> Week:
        week_uri = SleeperCollector._matchups_endpoint.format(
            self.season_to_id[year], week
        )
        logger.info(f"Getting games in week {week} at {week_uri}")

        response = requests.get(week_uri)
        response.raise_for_status()
        week_data = response.json()

        matchup_results: Dict[int, Game] = {}
        for team_week in week_data:
            if team_week["matchup_id"] not in matchup_results:
                matchup_results[team_week["matchup_id"]] = Game(team_data=[])

            logger.debug(
                f"Adding {team_week['roster_id']} to matchup {team_week['matchup_id']} week {week} "
                f"in {year}"
            )

            roster = set(team_week["players"])
            starters = set(team_week["starters"])
            try:
                starters.remove(
                    "0"
                )  # '0' is a 'starter' if the position has no player assigned.
            except KeyError:
                pass

            bench = roster.difference(starters)
            team_data = TeamGameData(
                points=team_week["points"],
                managers=team_to_manager[team_week["roster_id"]],
                roster=Roster(
                    starters=[
                        Player(
                            id=s,
                            name=self._players[s]["first_name"]
                            + " "
                            + self._players[s]["last_name"],
                            position=self._players[s]["position"],
                        )
                        for s in starters
                    ],
                    bench=[
                        Player(
                            id=b,
                            name=self._players[b]["first_name"]
                            + " "
                            + self._players[b]["last_name"],
                            position=self._players[b]["position"],
                        )
                        for b in bench
                    ],
                ),
            )

            matchup_results[team_week["matchup_id"]].team_data.append(team_data)

        game_results: List[Game] = []
        for matchup in matchup_results.values():
            game_results.append(matchup)

        return Week(games=game_results)

    @staticmethod
    def _get_players() -> Dict[str, Any]:
        response = requests.get(SleeperCollector._all_players_endpoint)
        response.raise_for_status()
        return response.json()
