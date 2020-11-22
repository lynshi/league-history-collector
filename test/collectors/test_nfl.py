# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name

import json
import tempfile
from unittest.mock import MagicMock, patch

from collectors import NFLCollector, NFLConfiguration


def test_NFLConfiguration_load():
    dict_config = {"username": "nemo", "password": "hunter2", "nfl": {"leagueId": "12345"}}

    expected_config = NFLConfiguration.load(dict_config=dict_config)

    with tempfile.NamedTemporaryFile("w") as config_file:
        config_file.write(json.dumps(dict_config))
        config_file.flush()

        args = {"filename": config_file.name, "dict_config": dict_config}

        for arg, arg_value in args.items():
            assert NFLConfiguration.load(**{arg: arg_value}) == expected_config


def test_NFLCollector_init():
    dict_config = {"username": "nemo", "password": "hunter2", "nfl": {"leagueId": "12345"}}
    config = NFLConfiguration.load(dict_config=dict_config)

    driver_mock = MagicMock()
    time_between_actions = 5

    with patch("time.time") as time_mock:
        time_mock.return_value = 42
        collector = NFLConfiguration(config, driver_mock, time_between_actions)

    assert collector._config == config
    
