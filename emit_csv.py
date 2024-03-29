"""Writes the season data to CSV."""

import argparse
import csv
import json
import os
import shutil

from loguru import logger

from league_history_collector.collectors import SleeperCollector, SleeperConfiguration
from league_history_collector.collectors.models import League
from league_history_collector.transformer.csv.draft import set_drafts
from league_history_collector.transformer.csv.finish import set_finish
from league_history_collector.transformer.csv.game import set_games
from league_history_collector.transformer.csv.lineup import set_lineups
from league_history_collector.transformer.csv.manager import set_managers
from league_history_collector.transformer.csv.player import set_players
from league_history_collector.transformer.csv.season import set_season


def main(config: SleeperConfiguration):  # pylint: disable=too-many-locals
    """Main method for converting league data to CSV."""

    file_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(file_dir, "data")

    if os.path.isdir(data_dir):
        shutil.rmtree(data_dir)

    os.makedirs(data_dir)

    collector = SleeperCollector(config)
    for season in collector.get_seasons():
        file = os.path.join(file_dir, f"{config.league_id}-{season}.json")
        logger.debug(f"Loading {file}")
        with open(file, encoding="utf-8") as season_data_file:
            league = League.from_dict(json.load(season_data_file))

        logger.info(f"Loaded data from {file}")

        managers_csv = os.path.join(data_dir, "managers.csv")
        manager_id_mapper = lambda s: s

        set_managers(managers_csv, league.managers, manager_id_mapper)

        players_csv = os.path.join(data_dir, "players.csv")
        set_players(
            players_csv, league, deduplicate=False
        )  # Remap ids used in NFL Fantasy

        seasons_csv = os.path.join(data_dir, "seasons.csv")
        set_season(seasons_csv, league, manager_id_mapper)

        finish_csv = os.path.join(data_dir, "finish.csv")
        set_finish(finish_csv, league, manager_id_mapper)

        games_csv = os.path.join(data_dir, "games.csv")
        set_games(games_csv, league, manager_id_mapper)

        logger.info(f"Loading player ids mapping from {players_csv}")
        with open(players_csv, encoding="utf-8") as emitted_players:
            csv_reader = csv.DictReader(emitted_players)

            player_mapping = {}
            for row in csv_reader:
                player_tuple = (row["player_name"], row["player_position"])
                if player_tuple not in player_mapping:
                    player_mapping[player_tuple] = set()

                player_mapping[player_tuple].add(row["player_id"])

        def player_mapper(p_id: str, p_name: str, p_pos: str):
            input_tuple = (p_name, p_pos)
            potential_ids = player_mapping.get(  # pylint: disable=cell-var-from-loop
                input_tuple, []
            )
            if len(potential_ids) == 1:
                for assigned_id in potential_ids:
                    return assigned_id

            # If no match is possible, keep the provided id.
            return p_id

        lineups_csv = os.path.join(data_dir, "lineups.csv")
        set_lineups(lineups_csv, league, manager_id_mapper, player_mapper)

        drafts_csv = os.path.join(data_dir, "drafts.csv")
        set_drafts(drafts_csv, league, manager_id_mapper, player_mapper)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Collects fantasy football league history")
    parser.add_argument(
        "-c", "--config", help="Path to configuration file", default="sleeper.json"
    )

    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as infile:
        config_dict = json.load(infile)

    main(SleeperConfiguration.from_dict(config_dict))
