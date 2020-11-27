"""For collection league data from NFL Fantasy."""

from __future__ import annotations
from dataclasses import dataclass, field
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from loguru import logger
from selenium import webdriver

from collectors.base import Configuration, ICollector
from collectors.models import League, Manager, Season


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


class NFLCollector(ICollector):
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

        league = League(id=self._config.league_id)

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

    def _get_seasons(self) -> List[str]:
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
            seasons.append(item.get_attribute("textContent").split(" ")[0])

        return seasons

    def _set_season_data(self, year: int, league: League):
        team_to_manager = self._set_managers(year, league)
        return

        self._set_final_standings(year, team_to_manager, league)
        self._set_regular_season_results(year, team_to_manager, league)

    def _set_managers(  # pylint: disable=too-many-locals
        self, year: int, league: League
    ) -> Dict[str, List[str]]:
        final_standings_url = self._get_final_standings_url(year)
        self._change_page(self._driver.get, final_standings_url)

        standings_div = self._driver.find_element_by_id("finalStandings")
        results_div = standings_div.find_element_by_class_name("results")
        team_list = results_div.find_elements_by_xpath(".//li")

        team_ids = []
        for team in team_list:
            team_page_link = team.find_element_by_xpath(".//a")
            team_id = team_page_link.get_attribute("href").split("teamId=")[-1]

            try:
                _ = int(team_id)
            except ValueError as e:
                logger.error(
                    f"Team ID {team_id} for year {year} does not seem correct (not an integer)"
                )
                raise RuntimeError(
                    f"Could not map team IDs to managers in year {year}"
                ) from e
            
            team_ids.append(team_id)

        team_to_manager = {}
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

                league.managers[manager_id] = Manager(manager_id, manager_name)
                team_to_manager[team_id].append(manager_id)

                logger.debug(f"In {year}, found manager {league.managers[manager_id]}")
    
        return team_to_manager

    def _set_final_standings(
        self, year: int, team_to_manager: Dict[str, List[str]], league: League
    ):
        final_standings_url = self._get_final_standings_url(year)
        self._change_page(self._driver.get, final_standings_url)

        standings_div = self._driver.find_element_by_id("finalStandings")
        results_div = standings_div.find_element_by_class_name("results")
        team_list = results_div.find_elements_by_xpath(".//li")

        manager_final_ranks = {}

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

    def _set_regular_season_results(
        self, year: str, team_to_manager: Dict[str, List[str]], league: League
    ):
        regular_season_standings_url = self._get_regular_season_standings_url(year)

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

    def _get_team_home_url(self, year: str, team_id: str) -> str:
        return (
            f"https://fantasy.nfl.com/league/{self._config.league_id}/history/"
            f"{year}/teamhome?teamId={team_id}"
        )
