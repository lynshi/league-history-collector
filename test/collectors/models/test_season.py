# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import Record, Season


def test_Season():  # pylint: disable=too-many-locals
    season_id = "2020"
    final_rank = 1
    regular_season_rank = 3
    regular_season_points_scored = 1100
    regular_season_points_against = 1150
    regular_season_record = Record(8, 6, 0)
    regular_season_breakdown = Record(90, 36, 0)

    expected_json = {
        "id": season_id,
        "finalRank": final_rank,
        "regularSeasonRank": regular_season_rank,
        "regularSeasonPointsScored": regular_season_points_scored,
        "regularSeasonPointsAgainst": regular_season_points_against,
        "regularSeasonRecord": regular_season_record.to_dict(),
        "regularSeasonBreakdown": regular_season_breakdown.to_dict(),
        "weeks": {},
    }

    season = Season(
        id=season_id,
        final_rank=final_rank,
        regular_season_rank=regular_season_rank,
        regular_season_points_scored=regular_season_points_scored,
        regular_season_points_against=regular_season_points_against,
        regular_season_record=regular_season_record,
        regular_season_breakdown=regular_season_breakdown,
    )

    assert json.loads(season.to_json()) == expected_json
