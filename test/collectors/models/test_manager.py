# pylint: disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,invalid-name

import json

from collectors.models import Manager


def test_Manager():
    manager_id = "Alice-42"
    name = "Alice"
    manager = Manager(id=manager_id, name=name)

    expected_json = {"id": manager_id, "name": name, "seasons": {}}

    assert json.loads(manager.to_json()) == expected_json
