"""Transform season data into CSV."""

import csv
import os
from typing import Callable

from loguru import logger

from league_history_collector.collectors.models import League


def set_season(file_name: str, league: League, id_mapper: Callable[[str], str]):
    """Sets seasons in the league.

    :param file_name: Name of the CSV to write data to. If it exists, data is appended.
    :type file_name: str
    :param league: League data.
    :type league: League
    :param id_mapper: A method for mapping incoming manager ids to ids in the file. Useful if
        different ids can represent the same manager.
    :type id_mapper: Callable[[str], str]
    """

    season_results = []
    for season_id, season in league.seasons.items():
        logger.info(f"Getting regular season standings for {season_id}")
        for m_id, m_standing in season.standings.items():
            logger.debug(f"Getting results for {m_id} in {season_id}")
            season_results.append(
                {
                    "manager_id": id_mapper(m_id),
                    "season_id": season_id,
                    "regular_season_standing": m_standing.regular_season_standing.rank,
                    "points_for": m_standing.regular_season_standing.points_scored,
                    "points_against": m_standing.regular_season_standing.points_against,
                    "wins": m_standing.regular_season_standing.record.wins,
                    "ties": m_standing.regular_season_standing.record.ties,
                    "losses": m_standing.regular_season_standing.record.losses,
                }
            )

    write_header = not os.path.isfile(
        file_name
    )  # Only write headers if the file doesn't exist.

    logger.info(f"Writing season data to {file_name}")
    with open(file_name, "a+", encoding="utf-8") as outfile:
        fieldnames = list(season_results[0].keys())
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        for result in season_results:
            writer.writerow(result)
