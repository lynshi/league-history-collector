# pylint: disable=protected-access,duplicate-code

"""Collects league history for Sleeper."""

import argparse
import json
import sys

from loguru import logger

from league_history_collector.collectors import SleeperConfiguration, SleeperCollector
from league_history_collector.collectors.models import League


def run_collector(collector_config: SleeperConfiguration):
    """Runs a collector on the league specified by the provided configuration."""

    collector = SleeperCollector(collector_config)
    seasons = collector.get_seasons()

    for year in seasons:
        with open(f"{year}.json", "w") as outfile:
            league = League(id=collector.season_to_id[year], managers={}, seasons={})
            collector.set_season_data(year, league)

            with open(f"{year}.json", "w") as outfile:
                json.dump(league.to_dict(), outfile, sort_keys=True, indent=2)


if __name__ == "__main__":
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG")

    parser = argparse.ArgumentParser("Collects fantasy football league history")
    parser.add_argument(
        "-c", "--config", help="Path to configuration file", default="sleeper.json"
    )

    args = parser.parse_args()
    with open(args.config, encoding="utf-8") as infile:
        config_dict = json.load(infile)

    config = SleeperConfiguration.from_dict(config_dict)

    run_collector(config)
