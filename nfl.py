# pylint: disable=protected-access,duplicate-code

"""Collects league history for NFL Fantasy."""

import argparse
import json
import sys

from loguru import logger

from league_history_collector.collectors import (
    NFLCollector,
    NFLConfiguration,
    selenium_driver,
)
from league_history_collector.collectors.models import League


def run_collector(collector_config: NFLConfiguration):
    """Runs a collector on the league specified by the provided configuration."""

    with selenium_driver() as driver:
        collector = NFLCollector(collector_config, driver, (2, 4))

        overall_league_data = League(
            id=collector_config.league_id, managers={}, seasons={}
        )

        # Getting all the data at once was getting flaky, so let's split it by season.
        seasons = collector.get_seasons()
        for year in seasons:
            league = League(id=collector_config.league_id, managers={}, seasons={})
            collector.set_season_data(year, league)

            with open(f"{year}.json", "w") as outfile:
                json.dump(league.to_dict(), outfile, sort_keys=True, indent=2)

            overall_league_data.seasons[year] = league.seasons[year]
            for manager, manager_data in league.managers.items():
                if manager not in overall_league_data.managers:
                    overall_league_data.managers[manager] = manager_data
                else:
                    overall_league_data.managers[manager].seasons.append(year)

        with open("league.json", "w") as outfile:
            json.dump(overall_league_data.to_dict(), outfile, sort_keys=True, indent=2)


if __name__ == "__main__":
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG")

    parser = argparse.ArgumentParser("Collects fantasy football league history")
    parser.add_argument(
        "-c", "--config", help="Path to configuration file", default="nfl.json"
    )

    args = parser.parse_args()
    config = NFLConfiguration.load(filename=args.config)

    run_collector(config)
