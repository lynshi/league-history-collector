"""Transform final standing data into CSV."""

import csv
import os
from typing import Callable

from loguru import logger

from league_history_collector.collectors.models import League


def set_finish(file_name: str, league: League, id_mapper: Callable[[str], str]):
    """Sets season finish data.

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
        logger.info(f"Getting final standings for {season_id}")
        for m_id, m_standing in season.standings.items():
            logger.debug(f"Getting results for {m_id} in {season_id}")
            if m_standing.final_standing.rank is not None:
                season_results.append(
                    {
                        "manager_id": id_mapper(m_id),
                        "season_id": season_id,
                        "final_standing": m_standing.final_standing.rank,
                    }
                )

    write_header = not os.path.isfile(
        file_name
    )  # Only write headers if the file doesn't exist.

    logger.info(f"Writing finish data to {file_name}")
    with open(file_name, "a+", encoding="utf-8") as outfile:
        fieldnames = list(season_results[0].keys())
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()

        for result in season_results:
            writer.writerow(result)
