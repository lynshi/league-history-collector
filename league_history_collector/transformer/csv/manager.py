"""Transform manager data into CSV."""

import csv
import os
from typing import Callable, Dict

from loguru import logger

from league_history_collector.collectors.models import Manager


def set_managers(file_name: str, managers: Dict[str, Manager], id_mapper: Callable[[str], str] = lambda x: x):
    """Sets the managers in the provided CSV. If the CSV already exists, duplicate managers (by id)
    are updated with values from the latest data.

    :param file_name: Name of the CSV to write data to, and if, already existing, load data from.
    :type file_name: str
    :param managers: Mapping of manager ids to managers.
    :type managers: Dict[str, Manager]
    :param id_mapper: A method for mapping ids to ids, defaults to lambdax:x. Useful if different
        ids can represent the same manager.
    :type id_mapper: Callable[[str], str], optional
    """
    
    managers_output = {}
    if os.path.isfile(file_name):
        logger.info(f"{file_name} exists, loading existing managers")
        with open(file_name, encoding="utf-8") as infile:
            csv_reader = csv.DictReader(infile)
            for row in csv_reader:
                managers_output[row["manager_id"]] = row["manager_name"]

    for m_id, manager in managers.items():
        managers_output[id_mapper(m_id)] = manager.name

    with open(file_name, "w", encoding="utf-8") as outfile:
        fieldnames = ["manager_id", "manager_name"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()
        for m_id, m_name in managers_output.items():
            writer.writerow({'manager_id': m_id, 'manager_name': m_name})
