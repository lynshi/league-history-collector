"""For collection league data from NFL Fantasy."""

from __future__ import annotations
from dataclasses import dataclass, field
import random
import time
from typing import Any, Callable, List, Optional, Tuple

from dataclasses_json import Exclude
from dataclasses_json import config as dataclass_json_config
from loguru import logger
from selenium import webdriver

from collectors.base import Configuration, ICollector, ManagerIdRetriever
from collectors.models import League


@dataclass
class NFLConfiguration(Configuration):
    """Extends the Configuration class with fields specific for NFL Fantasy."""

    league_id: str

    # This field is not currently initialized from JSON. If you need to initialize it,
    # set the value after object creation.
    manager_id_retriever: ManagerIdRetriever = field(
        default=ManagerIdRetriever,
        metadata=dataclass_json_config(exclude=Exclude.ALWAYS),  # type: ignore
    )

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

    def _get_season_data(self, league: League, year: int) -> League:
        pass
