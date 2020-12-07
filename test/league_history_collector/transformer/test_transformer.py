# pylint: disable=missing-class-docstring,missing-function-docstring,redefined-outer-name,missing-module-docstring,invalid-name,protected-access

from unittest.mock import MagicMock

import pytest

from league_history_collector.transformer import Configuration, Transformer


def test_Configuration_init():
    config = Configuration(2, [15, 16])
    assert config.num_playoff_teams == 2
    assert config.playoff_weeks == {15, 16}
    assert config.playoff_weeks_by_season == {}
    assert config.num_playoff_teams_by_season == {}
    assert config.playoff_teams == {}


def test_Configuration_is_in_playoffs():
    config = Configuration(
        4,
        [15, 16],
        num_playoff_teams_by_season={2017: 2},
        playoff_teams={2018: ["foo"]},
    )

    assert config.is_in_playoffs("bar", season=2016, rank=3) is True
    assert config.is_in_playoffs("foo", season=2016, rank=5) is False
    assert config.is_in_playoffs("bar", season=2017, rank=2) is True
    assert config.is_in_playoffs("foo", season=2017, rank=3) is False
    assert config.is_in_playoffs("bar", season=2018, rank=1) is False
    assert config.is_in_playoffs("foo", season=2018, rank=10) is True


def test_Configuration_playoff_weeks_for_season():
    config = Configuration(4, [15, 16], playoff_weeks_by_season={2019: [14, 15, 16]})

    assert config.playoff_weeks_for_season(2018) == [15, 16]
    assert config.playoff_weeks_for_season(2019) == [14, 15, 16]


@pytest.fixture(name="transformer_config")
def fixture_transformer_config():
    yield Configuration(4, [15, 16])


def test_Transformer_validates_parameters(transformer_config: Configuration):
    league_data = MagicMock()
    anonymizer = MagicMock()
    manager_id_mapping = MagicMock()

    with pytest.raises(ValueError):
        Transformer(transformer_config, league_data, anonymizer, manager_id_mapping)


def test_Transformer_init(transformer_config: Configuration):
    league_data = MagicMock()

    transformer = Transformer(transformer_config, league_data)
    assert transformer._transformed is False
    assert transformer._data == league_data


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


@pytest.fixture(name="transformer")
def fixture_transformer():
    league_data = MagicMock()
    yield Transformer(Configuration(4, [15, 16]), league_data)


def test_Transformer_unready_properties(transformer: Transformer):
    with pytest.raises(RuntimeError):
        assert transformer.league_summary is not None

    with pytest.raises(RuntimeError):
        assert transformer.head_to_head is not None

    with pytest.raises(RuntimeError):
        assert transformer.games is not None

    with pytest.raises(RuntimeError):
        assert transformer.seasons is not None

    with pytest.raises(RuntimeError):
        assert transformer.managers is not None


def test_Transformer_get_name_for_manager_id(transformer: Transformer):
    manager_mock = MagicMock()
    manager_mock.name = "Alice"

    transformer._data.managers = {"1": manager_mock}
    assert transformer._get_name_for_manager_id("1") == "Alice"
