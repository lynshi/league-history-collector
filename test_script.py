# pylint: disable=protected-access

"""Script for testing functionality."""

from collectors import NFLCollector, NFLConfiguration, selenium_driver


if __name__ == "__main__":
    config = NFLConfiguration.load(filename="config.json")

    with selenium_driver() as driver:
        collector = NFLCollector(config, driver)
        collector._login()

        driver.save_screenshot("league.png")
