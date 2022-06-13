"""For collection league data from NFL Fantasy."""

from __future__ import annotations
from dataclasses import dataclass
import random
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from league_history_collector.collectors.base import Configuration, ICollector
from league_history_collector.collectors.models import (
    FinalStanding,
    League,
    Manager,
    ManagerStanding,
    RegularSeasonStanding,
    Season,
    Week,
)
from league_history_collector.models import (
    Game,
    Player,
    Record,
    Roster,
    TeamGameData,
)


@dataclass
class NFLConfiguration(Configuration):
    """Extends the Configuration class with fields specific for NFL Fantasy."""

    league_id: str

    @staticmethod
    def load(
        filename: Optional[str] = None, dict_config: Optional[dict] = None
    ) -> NFLConfiguration:
        """Build an NFLConfiguration object from JSON data."""

        dict_config = Configuration._get_dict_config(
            filename=filename, dict_config=dict_config
        )
        dict_config = {**dict_config, **dict_config["nfl"]}
        del dict_config["nfl"]

        return NFLConfiguration.from_dict(dict_config)


class NFLCollector(ICollector):  # pylint: disable=too-few-public-methods
    """Implements Collector interface for collecting league data from NFL Fantasy."""

    def __init__(
        self,
        config: NFLConfiguration,
        driver: webdriver.Remote,
        time_between_pages_range: Tuple[int, int] = (2, 4),
        wait_seconds_after_page_change: int = 2,
    ):
        """Create an NFLCollector.

        args:
            driver: Inject the web driver to delegate cleanup to the caller.
                A driver may be created with
                `webdriver.Remote(command_executor="http://localhost:4444/wd/hub",
                                  desired_capabilities=DesiredCapabilities.CHROME)`.
            time_between_pages_range: When changing pages, wait for a period of time, in seconds,
                uniformly randomly selected from within this range (inclusive).
        """

        super().__init__()

        self._config = config

        self._driver = driver
        self._time_between_pages_range = time_between_pages_range
        self._wait_seconds_after_page_change = wait_seconds_after_page_change

        # Subtract so first action can occur immediately
        self._last_page_load_time = time.time() - self._time_between_pages_range[1]

        self._logged_in = False

    def save_all_data(self) -> League:
        """Save all league data."""

        league = League(id=self._config.league_id, managers={}, seasons={})

        if not self._logged_in:
            self._login()

        seasons = self.get_seasons()
        for year in seasons:
            self.set_season_data(year, league)

        return league

    def _change_page(self, action: Callable[..., Any], *args, **kwargs) -> Any:
        interval = random.uniform(
            self._time_between_pages_range[0], self._time_between_pages_range[1]
        )

        time.sleep(max(0, (interval - (time.time() - self._last_page_load_time))))
        self._last_page_load_time = time.time()

        result = action(*args, **kwargs)

        logger.debug(
            f"Waiting {self._wait_seconds_after_page_change} seconds after page change"
        )
        time.sleep(self._wait_seconds_after_page_change)

        return result

    def _login(self):
        login_url = "https://fantasy.nfl.com/account/sign-in"
        logger.info(f"Logging in to NFL.com at {login_url}")
        self._change_page(self._driver.get, login_url)

        login_form = self._driver.find_element_by_id("gigya-login-form")
        username = login_form.find_element_by_id("gigya-loginID-60062076330815260")
        password = login_form.find_element_by_id("gigya-password-85118380969228590")

        username.send_keys(self._config.username)
        password.send_keys(self._config.password)

        button_found = False
        input_submit_class_elements = self._driver.find_elements_by_class_name(
            "gigya-input-submit"
        )

        for login_button in input_submit_class_elements:
            element_value = login_button.get_attribute("value")
            element_type = login_button.get_attribute("type")
            logger.debug(
                f"Potential login button has text {element_value} and type {element_type}"
            )

            if element_value == "Sign In" and element_type == "submit":
                self._change_page(login_button.click)
                button_found = True
                break

        if not button_found:
            msg = "Could not find login button"
            logger.error(msg)
            raise RuntimeError(msg)

        sleep_seconds = 3 - self._wait_seconds_after_page_change
        if sleep_seconds > 0:
            logger.debug(
                f"Sleeping for {sleep_seconds} seconds before checking to make sure we're logged in"
            )
            time.sleep(sleep_seconds)  # wait for redirect

        league_url = f"https://fantasy.nfl.com/league/{self._config.league_id}"
        self._change_page(self._driver.get, league_url)
        if league_url != self._driver.current_url:
            msg = f"Expected to be on page {league_url}, but on {self._driver.current_url} instead"
            logger.error(msg)
            raise RuntimeError(msg)

        logger.success(f"Successfully logged in to {league_url}!")
        self._logged_in = True

    def get_seasons(self) -> List[int]:
        """Gets a list of seasons in the league.

        :return: A list of seasons, identified by year.
        :rtype: List[int]
        """
        if not self._logged_in:
            self._login()

        league_history_url = (
            f"https://fantasy.nfl.com/league/{self._config.league_id}/history"
        )
        self._change_page(self._driver.get, league_history_url)

        history_season_nav = self._driver.find_element_by_id("historySeasonNav")
        seasons_dropdown = history_season_nav.find_element_by_class_name("st-menu")
        season_list_items = seasons_dropdown.find_elements_by_xpath(".//a")

        seasons = []
        for item in season_list_items:
            # Gets the year which is in the link text. The item is hidden in the dropdown,
            # so `.text` does not work.
            seasons.append(int(item.get_attribute("textContent").split(" ")[0]))

        return seasons

    def set_season_data(self, year: int, league: League):
        """Sets data for the specified season in the provided league object.

        :param year: Year of the season.
        :type year: int
        :param league: League data object, to be modified by this method.
        :type league: League
        """
        if not self._logged_in:
            self._login()

        # Get mapping of team ID to manager ID, and list of managers for the year.
        team_to_manager, managers = self._get_managers(year)

        # Set up empty object.
        league.seasons[year] = Season(standings={}, weeks={})

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
                final_standing=final_standings[manager_id],
                regular_season_standing=regular_season_standings[manager_id],
            )
            league.seasons[year].standings[manager_id] = manager_standing

        # Get and populate games information.
        weeks_in_league = self._get_weeks(year)
        for week in weeks_in_league:
            week_data = self._get_games_for_week(year, week, team_to_manager)
            league.seasons[year].weeks[week] = week_data

    def _get_managers(  # pylint: disable=too-many-locals
        self, year: int
    ) -> Tuple[Dict[str, List[str]], Dict[str, Manager]]:
        final_standings_url = self._get_final_standings_url(year)
        logger.info(f"Getting managers for {year} from {final_standings_url}")
        self._change_page(self._driver.get, final_standings_url)

        standings_div = self._driver.find_element_by_id("finalStandings")
        results_div = standings_div.find_element_by_class_name("results")
        team_list = results_div.find_elements_by_xpath(".//li")

        team_ids = []
        for team in team_list:
            team_page_link = team.find_element_by_xpath(".//a")
            team_id = self._get_team_id_from_link(team_page_link)
            team_ids.append(team_id)

        team_to_manager = {}
        managers = {}
        for team_id in team_ids:
            team_to_manager[team_id] = []

            team_home_url = self._get_team_home_url(year, team_id)
            logger.debug(
                f"Got team home page for team {team_id} in {year} at {team_home_url}"
            )
            self._change_page(self._driver.get, team_home_url)

            team_detail_div = self._driver.find_element_by_id("teamDetail")
            right_side_div = team_detail_div.find_element_by_class_name("owners")
            manager_links = right_side_div.find_elements_by_xpath(".//a")

            for manager_link in manager_links:
                manager_name = manager_link.get_attribute("textContent")
                manager_id = manager_link.get_attribute("class").split("userId-")[-1]

                team_to_manager[team_id].append(manager_id)
                managers[manager_id] = Manager(name=manager_name, seasons=[year])

                logger.debug(
                    f"In {year}, found manager {manager_name} for team {team_id}"
                )

        logger.debug(f"Team to manager mapping: {team_to_manager}")
        return team_to_manager, managers

    def _get_final_standings(  # pylint: disable=too-many-locals
        self, year: int, team_to_manager: Dict[str, List[str]]
    ) -> Dict[str, FinalStanding]:
        final_standings_url = self._get_final_standings_url(year)
        logger.info(f"Getting final standings for {year} from {final_standings_url}")
        self._change_page(self._driver.get, final_standings_url)

        standings_div = self._driver.find_element_by_id("finalStandings")
        results_div = standings_div.find_element_by_class_name("results")
        team_list = results_div.find_elements_by_xpath(".//li")

        final_standings = {}
        for team in team_list:
            place_div = team.find_element_by_class_name("place")
            place_str = ""
            for character in place_div.text:
                try:
                    _ = int(character)
                    place_str += character
                except ValueError:  # The numeric place is contained in the first few characters.
                    break

            place = int(place_str)

            team_link = team.find_element_by_class_name("teamName")
            team_id = self._get_team_id_from_link(team_link)

            managers = team_to_manager[team_id]
            for manager_id in managers:
                final_standings[manager_id] = FinalStanding(place)
                logger.debug(
                    f"Final standing for manager {manager_id} in {year}: "
                    f"{final_standings[manager_id].to_json()}"
                )

        return final_standings

    def _get_regular_season_standings(  # pylint: disable=too-many-locals
        self, year: int, team_to_manager: Dict[str, List[str]]
    ) -> Dict[str, RegularSeasonStanding]:
        regular_season_standings_url = self._get_regular_season_standings_url(year)
        logger.info(
            f"Getting regular season standings for {year} from {regular_season_standings_url}"
        )
        self._change_page(self._driver.get, regular_season_standings_url)

        standings = self._driver.find_element_by_id("leagueHistoryStandings")

        # Skip first two table rows which don't have teams.
        team_rows = standings.find_elements_by_xpath(".//tr")[2:]

        regular_season_standings = {}
        for team in team_rows:
            team_link = team.find_element_by_class_name("teamName")
            team_id = self._get_team_id_from_link(team_link)

            possible_rank_spans = team.find_elements_by_class_name(f"teamId-{team_id}")
            team_rank = None
            for span in possible_rank_spans:
                if "teamRank" in span.get_attribute("class"):
                    team_rank = int(span.text)
                    break

            if team_rank is None:
                raise RuntimeError(
                    "Could not get team rank for team {team_id} in {year}"
                )

            wins, losses, ties = team.find_element_by_class_name(
                "teamRecord"
            ).text.split("-")
            team_record = Record(wins=wins, losses=losses, ties=ties)

            points = team.find_elements_by_class_name("teamPts")
            points_scored = float(points[0].text.replace(",", ""))
            points_against = float(points[1].text.replace(",", ""))

            for manager_id in team_to_manager[team_id]:
                regular_season_standings[manager_id] = RegularSeasonStanding(
                    rank=team_rank,
                    points_scored=points_scored,
                    points_against=points_against,
                    record=team_record,
                )

                logger.debug(
                    f"Regular season standing for manager {manager_id} in {year}: "
                    f"{regular_season_standings[manager_id].to_json()}"
                )

        return regular_season_standings

    def _get_weeks(self, year: int) -> Set[int]:
        schedule_url = self._get_week_schedule_url(year, 1)
        logger.info(f"Getting weeks in {year} from {schedule_url}")
        self._change_page(self._driver.get, schedule_url)

        schedule_week_nav = self._driver.find_element_by_class_name("scheduleWeekNav")

        # This is nasty because the spans with the week number don't have classes or id.
        weeks = set()
        for list_item in schedule_week_nav.find_elements_by_xpath(".//li"):
            for span in list_item.find_elements_by_xpath(".//span"):
                try:
                    week = int(span.text)
                    weeks.add(week)
                except ValueError:
                    continue

        logger.debug(f"Weeks with games: {weeks}")
        return weeks

    def _get_games_for_week(  # pylint: disable=too-many-locals
        self, year: int, week: int, team_to_manager: Dict[str, List[str]]
    ) -> Week:
        schedule_url = self._get_week_schedule_url(year, week)
        logger.info(f"Getting games for week {week} in {year} from {schedule_url}")
        self._change_page(self._driver.get, schedule_url)

        schedule_content_div = self._driver.find_element_by_class_name(
            "scheduleContentWrap"
        )
        schedule_content = schedule_content_div.find_element_by_class_name(
            "scheduleContent"
        )
        matchup_items = schedule_content.find_elements_by_class_name("matchup")

        matchups = []
        for matchup_item in matchup_items:
            team_ids = set()

            team_links = matchup_item.find_elements_by_class_name("teamName")
            for team_link in team_links:
                team_id = self._get_team_id_from_link(team_link)
                team_ids.add(team_id)

            matchups.append(tuple(team_ids))
            logger.debug(f"Added matchup {matchups[-1]} for week {week} in {year}")

        game_results = []
        for matchup in matchups:
            game_results.append(
                self._get_game_results(year, week, team_to_manager, matchup)
            )

        return Week(games=game_results)

    def _get_game_results(
        self,
        year: int,
        week: int,
        team_to_manager: Dict[str, List[str]],
        matchup: Tuple[str, str],
    ) -> Game:
        matchup_url = self._get_matchup_url(year, week, matchup[0], full_box_score=True)
        logger.info(
            f"Getting game results for {year} Week {week} matchup {matchup} from {matchup_url}"
        )
        self._change_page(self._driver.get, matchup_url)

        team_matchup_header = self._driver.find_element_by_id("teamMatchupHeader")
        team_total_divs = team_matchup_header.find_elements_by_class_name("teamTotal")

        if len(team_total_divs) != 2:
            raise RuntimeError(f"Expected 2 team totals, got {len(team_total_divs)}")

        # Get points and copy team manager list first.
        team_data = {}
        for team_total in team_total_divs:
            team_id = self._get_team_id_from_class(team_total)
            if team_id not in matchup:
                raise RuntimeError(
                    f"Unexpected team ID {team_id} for matchup {matchup}"
                )

            team_points = float(team_total.text)
            logger.debug(
                f"Team {team_id} scored {team_points} in week {week} of {year}."
            )

            team_data[team_id] = TeamGameData(
                team_points, team_to_manager[team_id], Roster(starters=[], bench=[])
            )

        rosters = self._get_matchup_rosters(
            year, week, matchup, full_box_score_loaded=True
        )
        for team_id in matchup:
            team_data[team_id].roster = rosters[team_id]

        return Game(
            team_data=list(team_data.values()),
        )

    def _get_matchup_rosters(  # pylint: disable=too-many-locals
        self,
        year: int,
        week: int,
        matchup: Tuple[str, str],
        full_box_score_loaded: Optional[bool] = False,
    ) -> Dict[str, Roster]:
        """Returns a mapping of team ID to roster."""

        if full_box_score_loaded is False:
            full_box_score_url = self._get_matchup_url(
                year, week, matchup[0], full_box_score=True
            )
            logger.info(f"Getting full box score from {full_box_score_url}")
            self._change_page(self._driver.get, full_box_score_url)
        else:
            logger.debug("Getting full box score from current page")

        team_matchup_track_dv = self._driver.find_element_by_id("teamMatchupTrack")
        team_wrap_divs = team_matchup_track_dv.find_elements_by_class_name("teamWrap")

        # The team selected by `team_id` is first in the box score table and `team_wrap_divs`.
        # This corresponds to the team identified by`matchup[0]`.

        rosters = {
            matchup[0]: Roster(starters=[], bench=[]),
            matchup[1]: Roster(starters=[], bench=[]),
        }

        for team_idx, team_wrap_div in enumerate(team_wrap_divs):
            roster_tables = team_wrap_div.find_elements_by_xpath(".//tbody")

            # Position players, Kicker, Defense
            for table in roster_tables:
                table_rows = table.find_elements_by_xpath(".//tr")

                for table_row in table_rows:
                    is_starter = True
                    try:
                        # I didn't look closely at how the table rows are done but it's likely
                        # there are decorative rows.
                        position_td = table_row.find_element_by_class_name(
                            "teamPosition"
                        )
                        if position_td.find_element_by_xpath("span").text == "BN":
                            is_starter = False
                    except NoSuchElementException:
                        logger.debug(
                            "Skipping row which doesn't seem to contain a player"
                        )
                        continue

                    try:
                        # Can raise if no starter was plugged in, such as at defense.
                        player_card = table_row.find_element_by_class_name("playerCard")
                    except NoSuchElementException:
                        logger.debug(
                            "Skipping row which doesn't seem to contain a player"
                        )
                        continue

                    player_id = self._get_player_id_from_class(player_card)
                    player_name = player_card.text

                    player_name_and_info = table_row.find_element_by_class_name(
                        "playerNameAndInfo"
                    )
                    c_class = player_name_and_info.find_element_by_class_name("c")
                    player_position = c_class.text.split(" - ")[0].split("\n")[-1]

                    player = Player(
                        id=player_id, name=player_name, position=player_position
                    )

                    text_mod = "starter" if is_starter is True else "bench player"
                    logger.debug(
                        f"Found {text_mod} {player.to_json()} for team {matchup[team_idx]}"
                    )

                    if is_starter:
                        rosters[matchup[team_idx]].starters.append(player)
                    else:
                        rosters[matchup[team_idx]].bench.append(player)

        return rosters

    def _get_final_standings_url(self, year: int) -> str:
        return (
            f"https://fantasy.nfl.com/league/{self._config.league_id}/history/"
            f"{year}/standings?historyStandingsType=final"
        )

    def _get_regular_season_standings_url(self, year: int) -> str:
        return (
            f"https://fantasy.nfl.com/league/{self._config.league_id}/history/"
            f"{year}/standings?historyStandingsType=regular"
        )

    def _get_team_home_url(self, year: int, team_id: str) -> str:
        return (
            f"https://fantasy.nfl.com/league/{self._config.league_id}/history/"
            f"{year}/teamhome?teamId={team_id}"
        )

    def _get_week_schedule_url(self, year: int, week: int):
        return (
            f"https://fantasy.nfl.com/league/{self._config.league_id}/history/"
            f"{year}/schedule?gameSeason={year}&leagueId={self._config.league_id}&"
            f"scheduleDetail={week}&scheduleType=week&standingsTab=schedule"
        )

    def _get_matchup_url(
        self, year: int, week: int, team_id: str, full_box_score: bool = False
    ) -> str:
        matchup_url = (
            f"https://fantasy.nfl.com/league/{self._config.league_id}/history/"
            f"{year}/teamgamecenter?teamId={team_id}&week={week}"
        )

        if full_box_score is True:
            matchup_url += "&trackType=fbs"

        return matchup_url

    @staticmethod
    def _get_team_id_from_link(link: WebElement) -> str:
        href_attribute = link.get_attribute("href")
        team_id = href_attribute.split("teamId=")[-1]
        try:
            _ = int(team_id)
        except ValueError as e:
            logger.error(f"Team ID {team_id} does not seem correct (not an integer)")
            raise RuntimeError(
                f"Could not get team ID from `href` attribute: {href_attribute}"
            ) from e

        return team_id

    @staticmethod
    def _get_team_id_from_class(element: WebElement) -> str:
        class_attribute = element.get_attribute("class")
        team_id = class_attribute.split("teamId-")[-1]
        try:
            _ = int(team_id)
        except ValueError as e:
            logger.error(f"Team ID {team_id} does not seem correct (not an integer)")
            raise RuntimeError(
                f"Could not get team ID from `class` attribute: {class_attribute}"
            ) from e

        return team_id

    @staticmethod
    def _get_player_id_from_class(element: WebElement) -> str:
        class_attribute = element.get_attribute("class")
        player_id = class_attribute.split("playerNameId-")[-1].split(" ")[0]
        try:
            _ = int(player_id)
        except ValueError as e:
            logger.error(
                f"Player ID {player_id} does not seem correct (not an integer)"
            )
            raise RuntimeError(
                f"Could not get player ID from `class` attribute: {class_attribute}"
            ) from e

        return player_id
