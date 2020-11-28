# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name,protected-access

import json
import tempfile
from typing import Optional
from unittest.mock import MagicMock, call, patch

import pytest

from collectors import NFLCollector, NFLConfiguration
from collectors.models import League


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
    time_between_pages_range = (3, 5)

    with patch("time.time") as time_mock:
        time_mock.return_value = 42
        collector = NFLCollector(config, driver_mock, time_between_pages_range)

    assert collector._config == config
    assert collector._driver == driver_mock
    assert collector._time_between_pages_range == time_between_pages_range

    time_mock.assert_called_once()
    assert (
        collector._last_page_load_time
        == time_mock.return_value - time_between_pages_range[1]
    )


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
    nfl_collector._get_seasons = MagicMock(return_value=["2019", "2018"])

    assert nfl_collector.save_all_data() == League(
        nfl_collector._config.league_id, {}, {}
    )

    nfl_collector._login.assert_called_once()
    nfl_collector._get_seasons.assert_called_once()


def test_change_page_no_sleep(nfl_collector: NFLCollector):
    def _callable(first, second: Optional[str] = None):
        return f"{first} {second}"

    nfl_collector._last_page_load_time = 0
    with patch("time.time") as time_mock:
        time_mock.side_effect = [
            nfl_collector._time_between_pages_range[1] + 1,
            nfl_collector._time_between_pages_range[1] + 2,
        ]

        with patch("time.sleep") as sleep_mock:
            assert (
                nfl_collector._change_page(_callable, "first", second="second")
                == "first second"
            )

    time_mock.assert_has_calls([call()] * 2)
    sleep_mock.assert_called_once_with(0)

    assert (
        nfl_collector._last_page_load_time
        == nfl_collector._time_between_pages_range[1] + 2
    )


def test_change_page_with_sleep(nfl_collector: NFLCollector):
    def _callable(first, second: Optional[str] = None):
        return f"{first} {second}"

    last_page_load_time = 2
    current_time = 3
    interval = 5
    change_page_time = interval + 1

    nfl_collector._last_page_load_time = last_page_load_time
    with patch("random.uniform") as uniform_mock:
        uniform_mock.return_value = interval

        with patch("time.time") as time_mock:
            time_mock.side_effect = [
                current_time,
                change_page_time,
            ]

            with patch("time.sleep") as sleep_mock:
                assert (
                    nfl_collector._change_page(_callable, "first", second="second")
                    == "first second"
                )

    uniform_mock.assert_called_once_with(
        nfl_collector._time_between_pages_range[0],
        nfl_collector._time_between_pages_range[1],
    )
    time_mock.assert_has_calls([call()] * 2)
    sleep_mock.assert_called_once_with(interval - (current_time - last_page_load_time))

    assert nfl_collector._last_page_load_time == change_page_time


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


def test_get_seasons(nfl_collector: NFLCollector):
    nav_mock = MagicMock()
    dropdown_mock = MagicMock()
    season0_mock = MagicMock()
    season1_mock = MagicMock()

    nfl_collector._change_page = MagicMock()
    nfl_collector._driver.find_element_by_id.return_value = nav_mock
    nav_mock.find_element_by_class_name.return_value = dropdown_mock
    dropdown_mock.find_elements_by_xpath.return_value = [season0_mock, season1_mock]

    season0_mock.get_attribute.return_value = "2019 Season"
    season1_mock.get_attribute.return_value = "2018 Season"

    assert nfl_collector._get_seasons() == [2019, 2018]

    nfl_collector._change_page.assert_called_once_with(
        nfl_collector._driver.get,
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}/history",
    )
    nfl_collector._driver.find_element_by_id.assert_called_once_with("historySeasonNav")
    nav_mock.find_element_by_class_name.assert_called_once_with("st-menu")
    dropdown_mock.find_elements_by_xpath.assert_called_once_with(".//a")

    season0_mock.get_attribute.assert_called_once_with("textContent")
    season1_mock.get_attribute.assert_called_once_with("textContent")


def test_get_final_standings_url(nfl_collector: NFLCollector):
    year = 2018
    expected_url = (
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}/history/"
        f"{year}/standings?historyStandingsType=final"
    )

    assert nfl_collector._get_final_standings_url(year) == expected_url


def test__get_regular_season_standings_url(nfl_collector: NFLCollector):
    year = 2018
    expected_url = (
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}/history/"
        f"{year}/standings?historyStandingsType=regular"
    )

    assert nfl_collector._get_regular_season_standings_url(year) == expected_url


def test_get_team_home_url(nfl_collector: NFLCollector):
    year = 2018
    team_id = "5"
    expected_url = (
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}/history/"
        f"{year}/teamhome?teamId={team_id}"
    )

    assert nfl_collector._get_team_home_url(year, team_id) == expected_url


def test_get_week_schedule_url(nfl_collector: NFLCollector):
    year = 2018
    week = 3
    expected_url = (
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}/history/"
        f"{year}/schedule?gameSeason={year}&leagueId={nfl_collector._config.league_id}&"
        f"scheduleDetail={week}&scheduleType=week&standingsTab=schedule"
    )

    assert nfl_collector._get_week_schedule_url(year, week) == expected_url


def test_get_matchup_url(nfl_collector: NFLCollector):
    year = 2018
    week = 3
    team_id = "2"
    expected_url = (
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}/history/"
        f"{year}/teamgamecenter?teamId={team_id}&week={week}"
    )

    assert nfl_collector._get_matchup_url(year, week, team_id) == expected_url


def test_get_matchup_url_full_box_score(nfl_collector: NFLCollector):
    year = 2018
    week = 3
    team_id = "2"
    expected_url = (
        f"https://fantasy.nfl.com/league/{nfl_collector._config.league_id}/history/"
        f"{year}/teamgamecenter?teamId={team_id}&week={week}&trackType=fbs"
    )

    assert (
        nfl_collector._get_matchup_url(year, week, team_id, full_box_score=True)
        == expected_url
    )


def test_get_team_id_from_link():
    team_id = "2"

    web_element_mock = MagicMock()
    web_element_mock.get_attribute.return_value = (
        f"/url/to/something?query=param&teamId={team_id}"
    )

    assert team_id == NFLCollector._get_team_id_from_link(web_element_mock)

    web_element_mock.get_attribute.assert_called_once_with("href")


def test_get_team_id_from_link_invalid():
    team_id = "2"

    web_element_mock = MagicMock()
    web_element_mock.get_attribute.return_value = (
        f"/url/to/something?teamId={team_id}&query=param"
    )

    with pytest.raises(RuntimeError):
        NFLCollector._get_team_id_from_link(web_element_mock)

    web_element_mock.get_attribute.assert_called_once_with("href")


def test_get_team_id_from_class():
    team_id = "2"

    web_element_mock = MagicMock()
    web_element_mock.get_attribute.return_value = f"teamTotal teamId-{team_id}"

    assert team_id == NFLCollector._get_team_id_from_class(web_element_mock)

    web_element_mock.get_attribute.assert_called_once_with("class")


def test_get_team_id_from_class_invalid():
    team_id = "2"

    web_element_mock = MagicMock()
    web_element_mock.get_attribute.return_value = f"teamTotal teamId-{team_id}-"

    with pytest.raises(RuntimeError):
        NFLCollector._get_team_id_from_class(web_element_mock)

    web_element_mock.get_attribute.assert_called_once_with("class")


def test_get_player_id_from_class():
    player_id = "100"

    web_element_mock = MagicMock()
    web_element_mock.get_attribute.return_value = (
        f"playerNameId-{player_id} somethingElse"
    )

    assert player_id == NFLCollector._get_player_id_from_class(web_element_mock)

    web_element_mock.get_attribute.assert_called_once_with("class")


def test_get_player_id_from_class_invalid():
    player_id = "100"

    web_element_mock = MagicMock()
    web_element_mock.get_attribute.return_value = (
        f"playerNameId-{player_id}a somethingElse"
    )

    with pytest.raises(RuntimeError):
        NFLCollector._get_player_id_from_class(web_element_mock)

    web_element_mock.get_attribute.assert_called_once_with("class")
