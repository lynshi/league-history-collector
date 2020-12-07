# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name,protected-access

from unittest.mock import MagicMock

import pytest

from league_history_collector.transformer import Configuration, Transformer


def test_Configuration_is_in_playoffs():
    config = Configuration(4, {2017: 2}, {2018: ["foo"]})

    assert config.is_in_playoffs("bar", season=2016, rank=3) is True
    assert config.is_in_playoffs("foo", season=2016, rank=5) is False
    assert config.is_in_playoffs("bar", season=2017, rank=2) is True
    assert config.is_in_playoffs("foo", season=2017, rank=3) is False
    assert config.is_in_playoffs("bar", season=2018, rank=1) is False
    assert config.is_in_playoffs("foo", season=2018, rank=10) is True


@pytest.fixture(name="transformer_config")
def fixture_transformer_config():
    yield Configuration(4)


def test_Transformer_validates_parameters(transformer_config: Configuration):
    league_data = MagicMock()
    anonymizer = MagicMock()
    manager_id_mapping = MagicMock()

    with pytest.raises(ValueError):
        Transformer(transformer_config, league_data, anonymizer, manager_id_mapping)


def test_Transformer_finds_duplicate_names(transformer_config: Configuration):
    league_data = MagicMock()
    m1 = MagicMock()
    m2 = MagicMock()

    league_data.managers = {"1": m1, "2": m2}
    m1.name = "Alice"
    m2.name = "Alice"

    with pytest.raises(RuntimeError):
        Transformer(transformer_config, league_data)


def test_Transformer_anonymizes(transformer_config: Configuration):
    league_data = MagicMock()
    m1 = MagicMock()
    m2 = MagicMock()

    league_data.managers = {"1": m1, "2": m2}
    m1.name = "Alice"
    m2.name = "Bob"

    anonymizer = MagicMock(side_effect=lambda x: x.upper())

    transformer = Transformer(transformer_config, league_data, anonymizer=anonymizer)
    assert transformer._data.managers["1"].name == "ALICE"
    assert transformer._data.managers["2"].name == "BOB"


def test_Transformer_anonymizing_finds_duplicate_names(
    transformer_config: Configuration,
):
    league_data = MagicMock()
    m1 = MagicMock()
    m2 = MagicMock()

    league_data.managers = {"1": m1, "2": m2}
    m1.name = "Alice"
    m2.name = "Bob"

    anonymizer = MagicMock(side_effect=lambda _: "FOO")

    with pytest.raises(RuntimeError):
        Transformer(transformer_config, league_data, anonymizer=anonymizer)


def test_Transformer_maps(transformer_config: Configuration):
    league_data = MagicMock()
    m1 = MagicMock()
    m2 = MagicMock()

    league_data.managers = {"1": m1, "2": m2}
    m1.name = "Alice"
    m2.name = "Bob"

    mapping = MagicMock(side_effect=lambda x: x + "_mapped")

    transformer = Transformer(
        transformer_config, league_data, manager_id_mapping=mapping
    )
    assert transformer._data.managers["1"].name == "1_mapped"
    assert transformer._data.managers["2"].name == "2_mapped"


def test_Transformer_mapping_finds_duplicate_names(transformer_config: Configuration):
    league_data = MagicMock()
    m1 = MagicMock()
    m2 = MagicMock()

    league_data.managers = {"1": m1, "2": m2}
    m1.name = "Alice"
    m2.name = "Bob"

    mapping = MagicMock(side_effect=lambda x: "mapped")

    with pytest.raises(RuntimeError):
        Transformer(transformer_config, league_data, manager_id_mapping=mapping)
