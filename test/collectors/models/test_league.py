# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import League


def test_League_defaults():
    league_id = "4242"
    league = League(id=league_id)

    expected_json = {"id": league_id, "managers": {}}

    assert json.loads(league.to_json()) == expected_json
