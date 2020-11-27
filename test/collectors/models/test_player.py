# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import Player


def test_Player():
    player_id = "0"
    name = "Air Bud"
    position = "WR"

    expected_json = {"id": player_id, "name": name, "position": position}

    assert (
        json.loads(Player(id=player_id, name=name, position=position).to_json())
        == expected_json
    )
