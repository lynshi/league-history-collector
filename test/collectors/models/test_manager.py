# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import Manager


def test_Manager():
    manager_id = "Alice"
    manager = Manager(id=manager_id)

    expected_json = {"id": manager_id, "seasons": {}}

    assert json.loads(manager.to_json()) == expected_json
