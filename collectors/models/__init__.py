"""Models for data returned by collectors. The model shapes are optimized for easy
creation while collecting data."""

from collectors.models.league import League
from collectors.models.manager import Manager
from collectors.models.player import Player
from collectors.models.record import Record
from collectors.models.roster import Roster
from collectors.models.season import (
    FinalStanding,
    ManagerStanding,
    RegularSeasonStanding,
    Season,
)
from collectors.models.week import Game, TeamGameData, Week
