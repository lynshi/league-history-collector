# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import League, ManagerData


def test_League_defaults():
    league_id = "4242"
    league = League(id=league_id)

    expected_json = {"id": league_id, "managers": {}}

    assert json.loads(league.to_json()) == expected_json


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

    league_id = "4242"
    league = League(id=league_id, manager_data_to_id=manager_data_to_id)

    assert league.get_manager_id(alice) == "Alice"
    assert league.get_manager_id(bob) == "Bob"
    assert league.get_manager_id(chris) == "Chris"
    assert league.get_manager_id(david) == "David"
    assert league.get_manager_id(alice_1) == "Alice-1"

    eunice = ManagerData("Eunice", 2019)
    assert league.get_manager_id(eunice) == "Eunice"

    assert league.manager_data_to_id == {**manager_data_to_id, **{eunice: "Eunice"}}
