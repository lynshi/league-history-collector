# pylint: disable=protected-access

"""Script for testing functionality."""

from collectors.models.league import League
import sys

from loguru import logger

from collectors import NFLCollector, NFLConfiguration, selenium_driver


if __name__ == "__main__":
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG")

    config = NFLConfiguration.load(filename="config.json")

    with selenium_driver() as driver:
        collector = NFLCollector(config, driver)
        collector._login()

        seasons = collector._get_seasons()
        logger.info(f"The following seasons are present in league history: {seasons}")

        collector._set_season_data(2019, League(id=config.league_id))
