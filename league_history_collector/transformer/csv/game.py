"""Transform games data into CSV."""

import csv
import os
from typing import Callable

from loguru import logger

from league_history_collector.collectors.models import League


def set_games(
    file_name: str, league: League, id_mapper: Callable[[str], str]
):  # pylint: disable=too-many-locals
    """Sets games in the league.

    :param file_name: Name of the CSV to write data to. If it exists, data is appended.
    :type file_name: str
    :param league: League data.
    :type league: League
    :param id_mapper: A method for mapping incoming manager ids to ids in the file. Useful if
        different ids can represent the same manager.
    :type id_mapper: Callable[[str], str]
    """

    game_results = []
    for season_id, season in league.seasons.items():
        logger.info(f"Getting games for {season_id}")
        for week_id, week in season.weeks.items():
            for game_id, game in enumerate(week.games):
                logger.debug(
                    f"Getting data for game {game_id} in week {week_id} of {season_id}"
                )

                if len(game.team_data) != 2:
                    logger.warning(
                        f"More than 2 teams present in game {game_id} in week {week_id} of "
                        f"{season_id}, skipping"
                    )
                    continue

                first_team_data = game.team_data[0]
                second_team_data = game.team_data[1]

                first_team_result = (
                    "win"
                    if first_team_data.points > second_team_data.points
                    else "loss"
                )
                second_team_result = (
                    "win"
                    if first_team_data.points < second_team_data.points
                    else "loss"
                )
                if first_team_data.points == second_team_data.points:
                    first_team_result = "tie"
                    second_team_result = "tie"

                for m_id in first_team_data.managers:
                    m_id = id_mapper(m_id)

                    for opp_id in second_team_data.managers:
                        opp_id = id_mapper(opp_id)
                        game_results.append(
                            {
                                "manager_id": m_id,
                                "season_id": season_id,
                                "week_id": week_id,
                                "points_for": first_team_data.points,
                                "points_against": second_team_data.points,
                                "opponent_id": opp_id,
                                "result": first_team_result,
                            }
                        )

                for m_id in second_team_data.managers:
                    m_id = id_mapper(m_id)

                    for opp_id in first_team_data.managers:
                        opp_id = id_mapper(opp_id)
                        game_results.append(
                            {
                                "manager_id": m_id,
                                "season_id": season_id,
                                "week_id": week_id,
                                "points_for": second_team_data.points,
                                "points_against": first_team_data.points,
                                "opponent_id": opp_id,
                                "result": second_team_result,
                            }
                        )

    write_header = not os.path.isfile(
        file_name
    )  # Only write headers if the file doesn't exist.

    logger.info(f"Writing games data to {file_name}")
    with open(file_name, "a+", encoding="utf-8") as outfile:
        fieldnames = list(game_results[0].keys())
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        for result in game_results:
            writer.writerow(result)
