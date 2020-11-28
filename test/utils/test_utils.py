# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name

from dataclasses_json import LetterCase
from dataclasses_json import config as dataclasses_json_config
from stringcase import camelcase

from utils import CamelCasedDataclass


def test_CamelCasedDataclass():
    assert camelcase is LetterCase.CAMEL
    assert (
        CamelCasedDataclass.dataclass_json_config
        == dataclasses_json_config(letter_case=camelcase)["dataclasses_json"]
    )
