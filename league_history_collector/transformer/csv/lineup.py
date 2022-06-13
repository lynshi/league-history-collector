"""Transform lineup data into CSV."""

import csv
import os
from typing import Callable

from loguru import logger

from league_history_collector.collectors.models import League


def set_lineups(
    file_name: str,
    league: League,
    manager_id_mapper: Callable[[str], str],
    player_id_mapper: Callable[[str, str, str], str],
):  # pylint: disable=too-many-locals,too-many-nested-blocks
    """Sets lineups in the league.

    :param file_name: Name of the CSV to write data to. If it exists, data is appended.
    :type file_name: str
    :param league: League data.
    :type league: League
    :param manager_id_mapper: A method for mapping incoming manager ids to ids in the file. Useful
        if different ids can represent the same manager.
    :type manager_id_mapper: Callable[[str], str]
    :param player_id_mapper: A method for mapping incoming player ids to ids in the file. Useful if
        different ids can represent the same player. The input is
        (player_id, player_name, player_position).
    :type player_id_mapper: Callable[[str, str, str], str]
    """

    lineup_results = []
    for season_id, season in league.seasons.items():
        logger.info(f"Getting lineups for {season_id}")
        for week_id, week in season.weeks.items():
            for game_id, game in enumerate(week.games):
                logger.debug(
                    f"Getting lineup data for game {game_id} in week {week_id} of {season_id}"
                )

                if len(game.team_data) != 2:
                    logger.warning(
                        f"More than 2 teams present in game {game_id} in week {week_id} of "
                        f"{season_id}, skipping"
                    )
                    continue

                for team_data in game.team_data:
                    # Manager id, Season id, week id, player id, starter (T/F)
                    for m_id in team_data.managers:
                        m_id = manager_id_mapper(m_id)

                        for starter in team_data.roster.starters:
                            lineup_results.append(
                                {
                                    "manager_id": m_id,
                                    "season_id": season_id,
                                    "week_id": week_id,
                                    "player_id": player_id_mapper(
                                        starter.id, starter.name, starter.position
                                    ),
                                    "is_starter": True,
                                }
                            )

                        for bench_player in team_data.roster.bench:
                            lineup_results.append(
                                {
                                    "manager_id": m_id,
                                    "season_id": season_id,
                                    "week_id": week_id,
                                    "player_id": player_id_mapper(
                                        bench_player.id,
                                        bench_player.name,
                                        bench_player.position,
                                    ),
                                    "is_starter": False,
                                }
                            )

    write_header = not os.path.isfile(
        file_name
    )  # Only write headers if the file doesn't exist.

    logger.info(f"Writing lineup data to {file_name}")
    with open(file_name, "a+", encoding="utf-8") as outfile:
        fieldnames = list(lineup_results[0].keys())
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        for result in lineup_results:
            writer.writerow(result)
