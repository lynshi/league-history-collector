# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name,protected-access

import json
import tempfile
from typing import Optional
from unittest.mock import MagicMock, call, patch

import pytest

from collectors import NFLCollector, NFLConfiguration


def test_NFLConfiguration_load():
    dict_config = {
        "username": "nemo",
        "password": "hunter2",
        "nfl": {"leagueId": "12345"},
    }

    expected_config = NFLConfiguration.load(dict_config=dict_config)

    with tempfile.NamedTemporaryFile("w") as config_file:
        config_file.write(json.dumps(dict_config))
        config_file.flush()

        args = {"filename": config_file.name, "dict_config": dict_config}

        for arg, arg_value in args.items():
            assert NFLConfiguration.load(**{arg: arg_value}) == expected_config


def test_init():
    dict_config = {
        "username": "nemo",
        "password": "hunter2",
        "nfl": {"leagueId": "12345"},
    }
    config = NFLConfiguration.load(dict_config=dict_config)

    driver_mock = MagicMock()
    time_between_pages = 5

    with patch("time.time") as time_mock:
        time_mock.return_value = 42
        collector = NFLCollector(config, driver_mock, time_between_pages)

    assert collector._config == config
    assert collector._driver == driver_mock
    assert collector._time_between_pages == time_between_pages

    time_mock.assert_called_once()
    assert collector._last_action_time == time_mock.return_value - time_between_pages


@pytest.fixture(name="nfl_collector")
def fixture_nfl_collector():
    dict_config = {
        "username": "nemo",
        "password": "hunter2",
        "nfl": {"leagueId": "12345"},
    }
    config = NFLConfiguration.load(dict_config=dict_config)

    driver_mock = MagicMock()

    yield NFLCollector(config, driver_mock)


def test_save_all_data(nfl_collector: NFLCollector):
    nfl_collector._login = MagicMock()

    nfl_collector.save_all_data()
    nfl_collector._login.assert_called_once()


def test_change_page_no_sleep(nfl_collector: NFLCollector):
    def _callable(first, second: Optional[str] = None):
        return f"{first} {second}"

    nfl_collector._last_action_time = 0
    with patch("time.time") as time_mock:
        time_mock.side_effect = [
            nfl_collector._time_between_pages + 1,
            nfl_collector._time_between_pages + 2,
        ]

        with patch("time.sleep") as sleep_mock:
            assert (
                nfl_collector._change_page(_callable, "first", second="second")
                == "first second"
            )

    time_mock.assert_has_calls([call()] * 2)
    sleep_mock.assert_called_once_with(0)

    assert nfl_collector._last_action_time == nfl_collector._time_between_pages + 2


def test_login(nfl_collector: NFLCollector):
    nfl_collector._change_page = MagicMock()

    login_form_mock = MagicMock()

    username_element_mock = MagicMock()
    password_element_mock = MagicMock()

    fake_button0_mock = MagicMock()
    fake_button1_mock = MagicMock()
    real_button_mock = MagicMock()

    nfl_collector._driver.find_element_by_id.return_value = login_form_mock
    login_form_mock.find_element_by_id.side_effect = [
        username_element_mock,
        password_element_mock,
    ]

    def _side_effect_0(arg: str) -> str:
        if arg == "value":
            return "not Sign In"

        if arg == "type":
            return "not submit"

        raise ValueError(f"Unexpected argument {arg}")

    fake_button0_mock.get_attribute.side_effect = _side_effect_0

    def _side_effect_1(arg: str) -> str:
        if arg == "value":
            return "Sign In"

        if arg == "type":
            return "not submit"

        raise ValueError(f"Unexpected argument {arg}")

    fake_button1_mock.get_attribute.side_effect = _side_effect_1

    def _side_effect_2(arg: str) -> str:
        if arg == "value":
            return "Sign In"

        if arg == "type":
            return "submit"

        raise ValueError(f"Unexpected argument {arg}")

    real_button_mock.get_attribute.side_effect = _side_effect_2

    nfl_collector._driver.find_elements_by_class_name.return_value = [
        fake_button0_mock,
        fake_button1_mock,
        real_button_mock,
        fake_button1_mock,
    ]

    nfl_collector._driver.current_url = (
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}"
    )

    with patch("time.sleep") as sleep_mock:
        nfl_collector._login()

    expected_login_url = (
        "https://fantasy.nfl.com/account/sign-in?s=fantasy&"
        f"returnTo=http%3A%2F%2Ffantasy.nfl.com%2Fleague%2F{nfl_collector._config.league_id}"
    )

    nfl_collector._change_page.assert_any_call(
        nfl_collector._driver.get,
        expected_login_url,
    )

    nfl_collector._driver.find_element_by_id.assert_any_call("gigya-login-form")
    login_form_mock.find_element_by_id.assert_has_calls(
        [
            call("gigya-loginID-60062076330815260"),
            call("gigya-password-85118380969228590"),
        ]
    )

    username_element_mock.send_keys.assert_called_once_with(
        nfl_collector._config.username
    )
    password_element_mock.send_keys.assert_called_once_with(
        nfl_collector._config.password
    )

    nfl_collector._driver.find_elements_by_class_name.assert_called_once_with(
        "gigya-input-submit"
    )
    fake_button1_mock.get_attribute.assert_has_calls([call("value"), call("type")])
    real_button_mock.get_attribute.assert_has_calls([call("value"), call("type")])

    nfl_collector._change_page.assert_any_call(real_button_mock.click)

    sleep_mock.assert_called_once_with(3)


def test_login_no_login_button(nfl_collector: NFLCollector):
    nfl_collector._change_page = MagicMock()

    login_form_mock = MagicMock()

    username_element_mock = MagicMock()
    password_element_mock = MagicMock()

    fake_button0_mock = MagicMock()
    fake_button1_mock = MagicMock()

    nfl_collector._driver.find_element_by_id.return_value = login_form_mock
    login_form_mock.find_element_by_id.side_effect = [
        username_element_mock,
        password_element_mock,
    ]

    def _side_effect_0(arg: str) -> str:
        if arg == "value":
            return "not Sign In"

        if arg == "type":
            return "not submit"

        raise ValueError(f"Unexpected argument {arg}")

    fake_button0_mock.get_attribute.side_effect = _side_effect_0

    def _side_effect_1(arg: str) -> str:
        if arg == "value":
            return "Sign In"

        if arg == "type":
            return "not submit"

        raise ValueError(f"Unexpected argument {arg}")

    fake_button1_mock.get_attribute.side_effect = _side_effect_1

    nfl_collector._driver.find_elements_by_class_name.return_value = [
        fake_button0_mock,
        fake_button1_mock,
    ]

    nfl_collector._driver.current_url = (
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}"
    )

    with pytest.raises(RuntimeError) as exception_raised:
        nfl_collector._login()
        assert f"{exception_raised.value}" == "Could not find login button"

    expected_login_url = (
        "https://fantasy.nfl.com/account/sign-in?s=fantasy&"
        f"returnTo=http%3A%2F%2Ffantasy.nfl.com%2Fleague%2F{nfl_collector._config.league_id}"
    )

    nfl_collector._change_page.assert_any_call(
        nfl_collector._driver.get,
        expected_login_url,
    )

    nfl_collector._driver.find_element_by_id.assert_any_call("gigya-login-form")
    login_form_mock.find_element_by_id.assert_has_calls(
        [
            call("gigya-loginID-60062076330815260"),
            call("gigya-password-85118380969228590"),
        ]
    )

    username_element_mock.send_keys.assert_called_once_with(
        nfl_collector._config.username
    )
    password_element_mock.send_keys.assert_called_once_with(
        nfl_collector._config.password
    )

    nfl_collector._driver.find_elements_by_class_name.assert_called_once_with(
        "gigya-input-submit"
    )
    fake_button1_mock.get_attribute.assert_has_calls([call("value"), call("type")])


def test_login_unmatched_url(nfl_collector: NFLCollector):
    nfl_collector._change_page = MagicMock()

    login_form_mock = MagicMock()

    username_element_mock = MagicMock()
    password_element_mock = MagicMock()

    fake_button0_mock = MagicMock()
    fake_button1_mock = MagicMock()
    real_button_mock = MagicMock()

    nfl_collector._driver.find_element_by_id.return_value = login_form_mock
    login_form_mock.find_element_by_id.side_effect = [
        username_element_mock,
        password_element_mock,
    ]

    def _side_effect_0(arg: str) -> str:
        if arg == "value":
            return "not Sign In"

        if arg == "type":
            return "not submit"

        raise ValueError(f"Unexpected argument {arg}")

    fake_button0_mock.get_attribute.side_effect = _side_effect_0

    def _side_effect_1(arg: str) -> str:
        if arg == "value":
            return "Sign In"

        if arg == "type":
            return "not submit"

        raise ValueError(f"Unexpected argument {arg}")

    fake_button1_mock.get_attribute.side_effect = _side_effect_1

    def _side_effect_2(arg: str) -> str:
        if arg == "value":
            return "Sign In"

        if arg == "type":
            return "submit"

        raise ValueError(f"Unexpected argument {arg}")

    real_button_mock.get_attribute.side_effect = _side_effect_2

    nfl_collector._driver.find_elements_by_class_name.return_value = [
        fake_button0_mock,
        fake_button1_mock,
        real_button_mock,
        fake_button1_mock,
    ]

    nfl_collector._driver.current_url = (
        f"not https://fantasy.nfl.com/league/{nfl_collector._config.league_id}"
    )
    expected_url = f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}"

    with patch("time.sleep") as sleep_mock:
        with pytest.raises(RuntimeError) as exception_raised:
            nfl_collector._login()
            assert (
                f"{exception_raised}"
                == f"Expected to be on page {expected_url}, but on"
                f"{nfl_collector._driver.current_url} instead"
            )

    expected_login_url = (
        "https://fantasy.nfl.com/account/sign-in?s=fantasy&"
        f"returnTo=http%3A%2F%2Ffantasy.nfl.com%2Fleague%2F{nfl_collector._config.league_id}"
    )

    nfl_collector._change_page.assert_any_call(
        nfl_collector._driver.get,
        expected_login_url,
    )

    nfl_collector._driver.find_element_by_id.assert_any_call("gigya-login-form")
    login_form_mock.find_element_by_id.assert_has_calls(
        [
            call("gigya-loginID-60062076330815260"),
            call("gigya-password-85118380969228590"),
        ]
    )

    username_element_mock.send_keys.assert_called_once_with(
        nfl_collector._config.username
    )
    password_element_mock.send_keys.assert_called_once_with(
        nfl_collector._config.password
    )

    nfl_collector._driver.find_elements_by_class_name.assert_called_once_with(
        "gigya-input-submit"
    )
    fake_button1_mock.get_attribute.assert_has_calls([call("value"), call("type")])
    real_button_mock.get_attribute.assert_has_calls([call("value"), call("type")])

    nfl_collector._change_page.assert_any_call(real_button_mock.click)

    sleep_mock.assert_called_once_with(3)