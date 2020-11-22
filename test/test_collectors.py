# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name

from unittest.mock import MagicMock, patch

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from collectors import selenium_driver

# test module exports
# pylint: disable=unused-import
from collectors import Configuration, ICollector, NFLCollector, NFLConfiguration


def test_selenium_driver_no_kwargs():
    with patch("collectors.webdriver") as webdriver_mock:
        driver_mock = MagicMock()
        webdriver_mock.Remote.return_value = driver_mock

        with selenium_driver() as driver:
            assert driver == driver_mock

        webdriver_mock.Remote.assert_called_once_with(
            command_executor="http://localhost:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.CHROME,
        )
        driver_mock.close.assert_called_once()


def test_selenium_driver_with_kwargs():
    with patch("collectors.webdriver") as webdriver_mock:
        driver_mock = MagicMock()
        webdriver_mock.Remote.return_value = driver_mock

        command_executor = "command_executor"
        desired_capabilities = DesiredCapabilities.FIREFOX

        with selenium_driver(
            command_executor=command_executor, desired_capabilities=desired_capabilities
        ) as driver:
            assert driver == driver_mock

        webdriver_mock.Remote.assert_called_once_with(
            command_executor=command_executor, desired_capabilities=desired_capabilities
        )
        driver_mock.close.assert_called_once()


def test_selenium_driver_driver_is_None():
    with patch("collectors.webdriver") as webdriver_mock:
        webdriver_mock.Remote.return_value = None

        with selenium_driver() as driver:
            assert driver is None

        # no exception should be thrown by the finally
