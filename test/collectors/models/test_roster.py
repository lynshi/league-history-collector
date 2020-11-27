# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import Player, Roster


def test_Roster():
    starters = [Player("0", "0", "QB")]
    bench = [Player("1", "1", "RB"), Player("2", "2", "WR")]

    player_schema = Player.schema()
    # Gets a "No overloads for <...> match parameters".
    expected_json = {
        "starters": player_schema.dump(starters, many=True),  # type: ignore
        "bench": player_schema.dump(bench, many=True),  # type: ignore
    }

    assert json.loads(Roster(starters=starters, bench=bench).to_json()) == expected_json
