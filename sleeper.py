"""Collects league history for Sleeper."""

import argparse
import json
import sys

from loguru import logger

from league_history_collector.collectors import SleeperConfiguration, SleeperCollector


def run_collector(collector_config: SleeperConfiguration):
    """Runs a collector on the league specified by the provided configuration."""

    collector = SleeperCollector(collector_config)
    season_data = collector.save_all_data()

    with open(f"{collector_config.year}.json", "w") as outfile:
        json.dump(season_data.to_dict(), outfile, sort_keys=True, indent=2)


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
