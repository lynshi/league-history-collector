"""Models for data returned by collectors. The model shapes are optimized for easy
creation while collecting data."""

from league_history_collector.collectors.models.draft import Draft
from league_history_collector.collectors.models.league import League
from league_history_collector.collectors.models.manager import Manager
from league_history_collector.collectors.models.season import (
    FinalStanding,
    ManagerStanding,
    RegularSeasonStanding,
    Season,
)
from league_history_collector.collectors.models.week import Week
