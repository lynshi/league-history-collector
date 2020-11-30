# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name

import json
import tempfile

import pytest

from league_history_collector.collectors import Configuration


def test_Configuration_load():
    dict_config = {"username": "nemo", "password": "hunter2"}

    expected_config = Configuration.load(dict_config=dict_config)

    with tempfile.NamedTemporaryFile("w") as config_file:
        config_file.write(json.dumps(dict_config))
        config_file.flush()

        args = {"filename": config_file.name, "dict_config": dict_config}

        for arg, arg_value in args.items():
            assert Configuration.load(**{arg: arg_value}) == expected_config


def test_Configuration_load_validates_arguments():
    dict_config = {"username": "nemo", "password": "hunter2"}

    with pytest.raises(ValueError):
        Configuration.load(filename="config.json", dict_config=dict_config)

    with pytest.raises(ValueError):
        Configuration.load(filename=None, dict_config=None)

    with pytest.raises(ValueError):
        Configuration.load()
