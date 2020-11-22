"""For collection league data from NFL Fantasy."""

from __future__ import annotations
from dataclasses import dataclass
import time
from typing import Any, Callable, Optional

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
        time_between_actions: int = 3,
    ):
        """Create an NFLCollector.

        args:
            driver: Inject the web driver to delegate cleanup to the caller.
                A driver may be created with
                `webdriver.Remote(command_executor="http://localhost:4444/wd/hub",
                                  desired_capabilities=DesiredCapabilities.CHROME)`.
            time_between_actions: The minimum amount of time to wait between browser interactions.
        """

        self._config = config

        self._driver = driver
        self._time_between_actions = time_between_actions

        # Subtract so first action can occur immediately
        self._last_action_time = time.time() - self._time_between_actions

    def save_all_data(self):
        """Save all league data."""

        self._login()

    def _act(self, interval: int, action: Callable[..., Any], *args, **kwargs) -> Any:
        time.sleep(max(0, (interval - (time.time() - self._last_action_time))))
        self._last_action_time = time.time()

        return action(*args, **kwargs)

    def _login(self):
        login_url = (
            "https://fantasy.nfl.com/account/sign-in?s=fantasy&"
            f"returnTo=http%3A%2F%2Ffantasy.nfl.com%2Fleague%2F{self._config.league_id}"
        )
        logger.info(f"Logging in to league at {login_url}")
        self._act(self._time_between_actions, self._driver.get, login_url)

        login_form = self._driver.find_element_by_id("gigya-login-form")
        username = login_form.find_element_by_id("gigya-loginID-60062076330815260")
        password = login_form.find_element_by_id("gigya-password-85118380969228590")

        self._act(1, username.send_keys, self._config.username)
        self._act(1, password.send_keys, self._config.password)

        login_button = None
        input_submit_class_elements = self._driver.find_elements_by_class_name(
            "gigya-input-submit"
        )
        for element in input_submit_class_elements:
            if element.text == "Sign In" and element.get_attribute("type") == "submit":
                login_button = element
                break

        if login_button is not None:
            self._act(1, login_button.click)
        else:
            msg = "Could not find login button"
            logger.error(msg)
            raise RuntimeError(msg)

        time.sleep(3)  # wait for redirect
        league_url = f"https://fantasy.nfl.com/league/{self._config.league_id}"
        if league_url != self._driver.current_url:
            msg = f"Expected to be on page {league_url}, but on {self._driver.current_url} instead"
            logger.error(msg)
            raise RuntimeError(msg)

        logger.info("Successfully logged in!")
