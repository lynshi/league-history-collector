"""Base model object."""

from dataclasses import dataclass
from typing import ClassVar, Dict

from dataclasses_json import DataClassJsonMixin, LetterCase
from dataclasses_json import config as dataclasses_json_config
from stringcase import camelcase


# Use camelcase when providing `letter_case` to dataclass_json to pacify type checker,
# but assert equivalence for sanity.
assert camelcase is LetterCase.CAMEL


# Inherit from DataClassJsonMixin as type checker doesn't get functions dataclass_json
# provides.
@dataclass
class CamelCasedDataclass(DataClassJsonMixin):
    """Dataclass configured for camel-cased encode/decode."""

    # Sets camel-casing for JSON.
    # https://github.com/lidatong/dataclasses-json/blob/
    # 3dc59e01ccdfec619ee4e4c3502b9759b67c3fa8/dataclasses_json/api.py#L140
    dataclass_json_config: ClassVar[Dict] = dataclasses_json_config(
        letter_case=camelcase
    )["dataclasses_json"]
