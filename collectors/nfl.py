"""For collection league data from NFL Fantasy."""

from __future__ import annotations
from dataclasses import dataclass
import random
import time
from typing import Any, Callable, Optional, Tuple

from dataclasses_json import dataclass_json, LetterCase
from loguru import logger
from selenium import webdriver

from .base import ICollector, Configuration


@dataclass_json(letter_case=LetterCase.CAMEL)
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

        # pylint: disable=no-member
        return NFLConfiguration.from_dict(dict_config)  # type: ignore


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

    def save_all_data(self):
        """Save all league data."""

        self._login()

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

        time.sleep(1)  # wait for redirect
        league_url = f"https://fantasy.nfl.com/league/{self._config.league_id}"
        if league_url != self._driver.current_url:
            msg = f"Expected to be on page {league_url}, but on {self._driver.current_url} instead"
            logger.error(msg)
            raise RuntimeError(msg)

        logger.info("Successfully logged in!")
