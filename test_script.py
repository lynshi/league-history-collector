# pylint: disable=protected-access

"""Script for testing functionality."""

import json
import sys

from loguru import logger

from collectors import NFLCollector, NFLConfiguration, selenium_driver
from collectors.models import League


FLAGS = {
    "SET_SEASON_DATA": False,
    "GET_SEASONS": False,
    "GET_WEEKS": False,
    "GET_GAME_RESULTS": True,
}


if __name__ == "__main__":
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG")

    if FLAGS["SET_SEASON_DATA"] is True:
        for flag, value in FLAGS.items():
            if flag == "SET_SEASON_DATA":
                continue

            input(
                "SET_SEASON_DATA and at least one other flag are both True."
                "This may result in a longer than necessary test. Continue [Press ENTER]?"
            )
            break

    config = NFLConfiguration.load(filename="config.json")

    with selenium_driver() as driver:
        collector = NFLCollector(config, driver, (0, 1))
        collector._login()

        # These are required for some method calls, so always do this.
        team_to_manager, managers = collector._get_managers(2019)
        logger.info(f"Managers in 2019: {managers}")

        if FLAGS["GET_SEASONS"]:
            seasons = collector._get_seasons()
            logger.info(
                f"The following seasons are present in league history: {seasons}"
            )

        if FLAGS["GET_WEEKS"]:
            weeks = collector._get_weeks(2019)
            logger.info(f"The following weeks are present in 2019: {weeks}")

        if FLAGS["SET_SEASON_DATA"]:
            league = League(id=config.league_id, managers={}, seasons={})
            collector._set_season_data(2019, league)

            logger.info(json.dumps(league.to_dict(), sort_keys=True, indent=4))

        if FLAGS["GET_GAME_RESULTS"]:
            game_results = collector._get_game_results(
                2019, 1, team_to_manager, ("2", "4")
            )
            logger.info(f"2019 Week 1:\n{game_results.to_json()}")
