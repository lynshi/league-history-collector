"""Transform player data into CSV."""

import csv
import os
from typing import Callable, Dict

from loguru import logger

from league_history_collector.collectors.models import League


def set_players(file_name: str, league: League, deduplicate: bool):
    """Sets the players in the provided CSV. If the CSV already exists, players are loaded from file
    to help reduce duplicates.

    If deduplicate is true, if a (player name, position) combination is found in the CSV with only
    one id associated, then the id assigned in the League structure is ignored and the one from the
    file is used. If the CSV is assumed to contain the player ids on the most recent platform, then
    older league data would be migrated to use the newer player ids. If (player name, position) is
    found multiple times (i.e. 2+ people with the same name play the same position), then we give up
    and continue using the id from the League object because we can't be sure which id is correct.

    :param file_name: Name of the CSV to write data to, and if, already existing, load data from.
    :type file_name: str
    :param league: League data.
    :type league: League
    :param deduplicate: If True, deduplicates players.
    :type deduplicate: bool
    """

    players_output = {}
    if os.path.isfile(file_name):
        logger.info(f"{file_name} exists, loading existing players")
        with open(file_name, encoding="utf-8") as infile:
            csv_reader = csv.DictReader(infile)
            for row in csv_reader:
                player_tuple = (row["player_name"], row["player_position"])
                if player_tuple not in players_output:
                    players_output[player_tuple] = set()

                players_output[player_tuple].add(row["player_id"])

    for _, season in league.seasons.items():
        for _, week in season.weeks.items():
            for game in week.games:
                for team_data in game.team_data:
                    for player in team_data.roster.starters:
                        player_tup = (player.name, player.position)
                        potential_ids = players_output.get(player_tup, {player.id})
                        if len(potential_ids) != 1:
                            potential_ids.add(player.id)
                        players_output[player_tup] = potential_ids

                    for player in team_data.roster.bench:
                        player_tup = (player.name, player.position)
                        potential_ids = players_output.get(player_tup, {player.id})
                        if len(potential_ids) != 1:
                            potential_ids.add(player.id)
                        players_output[player_tup] = potential_ids

    with open(file_name, "w", encoding="utf-8") as outfile:
        fieldnames = ["player_id", "player_name", "player_position"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()
        for (p_name, p_pos), p_ids in players_output.items():
            for p_id in p_ids:
                writer.writerow(
                    {"player_id": p_id, "player_name": p_name, "player_position": p_pos}
                )
