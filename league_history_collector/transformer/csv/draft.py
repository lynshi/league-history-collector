"""Transform draft data into CSV."""

import csv
import os
from typing import Callable

from loguru import logger

from league_history_collector.collectors.models import League


def set_drafts(
    file_name: str,
    league: League,
    manager_id_mapper: Callable[[str], str],
    player_id_mapper: Callable[[str, str, str], str],
):
    """Sets draft data.

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

    draft_results = []
    for season_id, season in league.seasons.items():
        logger.info(f"Getting draft for {season_id}")
        if season.draft_results is not None:
            for draft_idx, draft in enumerate(season.draft_results.drafts):
                for pick in draft:
                    draft_results.append(
                        {
                            "draft_idx": draft_idx,
                            "season_id": season_id,
                            "round": pick.round,
                            "round_slot": pick.round_slot,
                            "overall_pick": pick.overall_pick,
                            "player_id": player_id_mapper(
                                pick.player_id, pick.player_name, pick.player_position
                            ),
                            "player_position": pick.player_position,
                            "manager_id": manager_id_mapper(pick.manager_id),
                        }
                    )

    write_header = not os.path.isfile(
        file_name
    )  # Only write headers if the file doesn't exist.

    if draft_results:
        logger.info(f"Writing draft data to {file_name}")
        with open(file_name, "a+", encoding="utf-8") as outfile:
            fieldnames = list(draft_results[0].keys())
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            if write_header:
                writer.writeheader()

            for result in draft_results:
                writer.writerow(result)
    else:
        logger.info(f"No draft data for league {league.id}")
