"""For collection league data from NFL Fantasy."""

from __future__ import annotations
from dataclasses import dataclass
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from loguru import logger
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement

from collectors.base import Configuration, ICollector
from collectors.models import (
    FinalStanding,
    League,
    Manager,
    ManagerStanding,
    RegularSeasonStanding,
    Record,
    Season,
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

        self._config = config

        self._driver = driver
        self._time_between_pages_range = time_between_pages_range

        # Subtract so first action can occur immediately
        self._last_page_load_time = time.time() - self._time_between_pages_range[1]

    def save_all_data(self) -> League:
        """Save all league data."""

        league = League(id=self._config.league_id, managers={}, seasons={})

        self._login()
        self._get_seasons()

        return league

    def _change_page(self, action: Callable[..., Any], *args, **kwargs) -> Any:
        interval = random.uniform(
            self._time_between_pages_range[0], self._time_between_pages_range[1]
        )

        time.sleep(max(0, (interval - (time.time() - self._last_page_load_time))))
        self._last_page_load_time = time.time()

        return action(*args, **kwargs)

    def _login(self):
        login_url = (
            "https://fantasy.nfl.com/account/sign-in?s=fantasy&"
            f"returnTo=http%3A%2F%2Ffantasy.nfl.com%2Fleague%2F{self._config.league_id}"
        )
        logger.info(f"Logging in to league at {login_url}")
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

        sleep_seconds = 3
        logger.info(
            f"Sleeping for {sleep_seconds} seconds before checking to make sure we're logged in"
        )
        time.sleep(sleep_seconds)  # wait for redirect

        league_url = f"https://fantasy.nfl.com/league/{self._config.league_id}"
        if league_url != self._driver.current_url:
            msg = f"Expected to be on page {league_url}, but on {self._driver.current_url} instead"
            logger.error(msg)
            raise RuntimeError(msg)

        logger.info("Successfully logged in!")

    def _get_seasons(self) -> List[int]:
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

    def _set_season_data(self, year: int, league: League):
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

    def _get_managers(  # pylint: disable=too-many-locals
        self, year: int
    ) -> Tuple[Dict[str, List[str]], Dict[str, Manager]]:
        final_standings_url = self._get_final_standings_url(year)
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
            points_scored = float(points[0].text.replace(","))
            points_against = float(points[1].text.replace(","))

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

    @staticmethod
    def _get_team_id_from_link(link: WebElement) -> str:
        team_id = link.get_attribute("href").split("teamId=")[-1]
        try:
            _ = int(team_id)
        except ValueError as e:
            logger.error(f"Team ID {team_id} does not seem correct (not an integer)")
            raise RuntimeError("Could not get team ID") from e

        return team_id
