"""Defines module exports and interfaces."""

from contextlib import contextmanager

import selenium.webdriver as webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from collectors import models
from collectors.base import Configuration, ICollector, ManagerData, ManagerIdRetriever
from collectors.nfl import NFLCollector, NFLConfiguration


@contextmanager
def selenium_driver(**kwargs):
    """Yields a managed webdriver.Remote resource.

    `args` and `kwargs` are passed to the `webdriver.Remote` constructor."""

    kwargs["command_executor"] = kwargs.get(
        "command_executor", "http://localhost:4444/wd/hub"
    )
    kwargs["desired_capabilities"] = kwargs.get(
        "desired_capabilities", DesiredCapabilities.CHROME
    )

    driver = None
    try:
        driver = webdriver.Remote(**kwargs)
        yield driver
    finally:
        if driver is not None:
            driver.close()
