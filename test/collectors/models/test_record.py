# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import Record


def test_Record():
    wins = 9
    losses = 4
    ties = 1

    expected_json = {"wins": wins, "losses": losses, "ties": ties}

    assert (
        json.loads(Record(wins=wins, losses=losses, ties=ties).to_json())
        == expected_json
    )
