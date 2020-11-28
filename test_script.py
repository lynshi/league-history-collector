# pylint: disable=protected-access

"""Script for testing functionality."""

import json
import sys

from loguru import logger

from collectors import NFLCollector, NFLConfiguration, selenium_driver
from collectors.models import League


if __name__ == "__main__":
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG")

    config = NFLConfiguration.load(filename="config.json")

    with selenium_driver() as driver:
        collector = NFLCollector(config, driver, (0, 1))
        collector._login()

        # seasons = collector._get_seasons()
        # logger.info(f"The following seasons are present in league history: {seasons}")

        # league = League(id=config.league_id, managers={}, seasons={})
        # collector._set_season_data(2019, league)

        # logger.info(json.dumps(league.to_dict(), sort_keys=True, indent=4))

        weeks = collector._get_weeks(2019)
        logger.info(f"The following weeks are present in 2019: {weeks}")
