"""Writes the season data to CSV."""

import json
import os

from loguru import logger

from league_history_collector.collectors.models import League
from league_history_collector.transformer.csv.manager import set_managers
from league_history_collector.transformer.csv.player import set_players

# Reverse sorting because the range looks nicer defined in increasing order :)
# We migrated to Sleeper in 2021.
SEASONS = sorted([year for year in range(2013, 2022)], reverse=True)


def main():
    file_dir = os.path.dirname(os.path.abspath(__file__))
    for season in SEASONS:
        file = os.path.join(file_dir, f"{season}.json")
        logger.debug(f"Loading {file}")
        with open(file, encoding="utf-8") as infile:
            league = League.from_dict(json.load(infile))

        logger.info(f"Loaded data from {file}")

        managers_csv = os.path.join(file_dir, "data/managers.csv")
        if season <= 2020:
            # Remap NFL manager ids to Sleeper ids.
            with open("manager_mapping.json", encoding="utf-8") as infile:
                id_mapping = json.load(infile)

            id_mapper = lambda s: id_mapping.get(s, s)
        else:
            id_mapper = lambda s: s

        set_managers(managers_csv, league.managers, id_mapper)

        players_csv = os.path.join(file_dir, "data/players.csv")
        set_players(
            players_csv, league, deduplicate=season < 2021
        )  # Remap ids used in NFL Fantasy


if __name__ == "__main__":
    main()
