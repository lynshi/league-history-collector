# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name

import json
import tempfile

import pytest

from collectors import Configuration, ManagerData, ManagerIdRetriever


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


def test_ManagerIdRetriever_default_init():
    retriever = ManagerIdRetriever()
    assert retriever.manager_data_to_id == {}


def test_get_manager_id():
    alice = ManagerData("Alice")
    bob = ManagerData("Bob", season=2020)
    chris = ManagerData("Chris", league_team_id=42)
    david = ManagerData("David", season=2020, league_team_id=42)
    alice_1 = ManagerData("Alice", season=2018, league_team_id=5)

    manager_data_to_id = {
        alice: "Alice",
        bob: "Bob",
        chris: "Chris",
        david: "David",
        alice_1: "Alice-1",
    }

    retriever = ManagerIdRetriever(manager_data_to_id=manager_data_to_id)

    assert retriever.get_manager_id(alice) == "Alice"
    assert retriever.get_manager_id(bob) == "Bob"
    assert retriever.get_manager_id(chris) == "Chris"
    assert retriever.get_manager_id(david) == "David"
    assert retriever.get_manager_id(alice_1) == "Alice-1"

    eunice = ManagerData("Eunice", 2019)
    assert retriever.get_manager_id(eunice) == "Eunice"

    assert retriever.manager_data_to_id == {**manager_data_to_id, **{eunice: "Eunice"}}
