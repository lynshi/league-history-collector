"""Writes the season data to CSV."""

import json
import os
import shutil

from loguru import logger

from league_history_collector.collectors.models import League
from league_history_collector.transformer.csv.finish import set_finish
from league_history_collector.transformer.csv.manager import set_managers
from league_history_collector.transformer.csv.player import set_players
from league_history_collector.transformer.csv.season import set_season

# Reverse sorting because the range looks nicer defined in increasing order :)
# We migrated to Sleeper in 2021.
SEASONS = sorted(range(2013, 2022), reverse=True)


def main():
    """Main method for converting league data to CSV."""

    file_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(file_dir, "data")

    if os.path.isdir(data_dir):
        shutil.rmtree(data_dir)

    os.makedirs(data_dir)

    with open("manager_mapping.json", encoding="utf-8") as infile:
        id_mapping_from_file = json.load(infile)

    mapping_from_file = lambda s: id_mapping_from_file.get(s, s)

    for season in SEASONS:
        file = os.path.join(file_dir, f"{season}.json")
        logger.debug(f"Loading {file}")
        with open(file, encoding="utf-8") as infile:
            league = League.from_dict(json.load(infile))

        logger.info(f"Loaded data from {file}")

        managers_csv = os.path.join(data_dir, "managers.csv")
        if season <= 2020:
            # Remap NFL manager ids to Sleeper ids.
            manager_id_mapper = mapping_from_file
        else:
            manager_id_mapper = lambda s: s

        set_managers(managers_csv, league.managers, manager_id_mapper)

        players_csv = os.path.join(data_dir, "players.csv")
        set_players(
            players_csv, league, deduplicate=season < 2021
        )  # Remap ids used in NFL Fantasy

        seasons_csv = os.path.join(data_dir, "seasons.csv")
        set_season(seasons_csv, league, manager_id_mapper)

        finish_csv = os.path.join(data_dir, "finish.csv")
        set_finish(finish_csv, league, manager_id_mapper)


if __name__ == "__main__":
    main()
