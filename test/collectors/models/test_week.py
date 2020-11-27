# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import Player, Record, Roster, Week


def test_Week():
    week_id = "14"
    opponent_id = ["Alice", "Bob"]
    points_scored = 1000
    points_against = 950

    starters = [Player("0", "0", "QB")]
    bench = [Player("1", "1", "RB"), Player("2", "2", "WR")]
    roster = Roster(starters=starters, bench=bench)

    breakdown_record = Record(5, 3, 1)

    expected_json = {
        "id": week_id,
        "opponentId": opponent_id,
        "pointsScored": points_scored,
        "pointsAgainst": points_against,
        "breakdownRecord": breakdown_record.to_dict(),
        "roster": roster.to_dict(),
    }

    week = Week(
        id=week_id,
        opponent_id=opponent_id,
        points_scored=points_scored,
        points_against=points_against,
        breakdown_record=breakdown_record,
        roster=roster,
    )
    assert json.loads(week.to_json()) == expected_json
