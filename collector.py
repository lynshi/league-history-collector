"""Collects league history."""

import argparse

from collectors import NFLCollector, NFLConfiguration, selenium_driver


def run_collector(collector_config: NFLConfiguration):
    """Runs a collector on the league specified by the provided configuration."""

    with selenium_driver() as driver:
        collector = NFLCollector(collector_config, driver, (2, 4))
        league_data = collector.save_all_data()

        with open("league.json", "w") as outfile:
            outfile.write(league_data.to_json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Collects fantasy football league history")
    parser.add_argument(
        "-c", "--config", help="Path to configuration file", default="config.json"
    )

    args = parser.parse_args()
    config = NFLConfiguration.load(filename=args.config)

    run_collector(config)
