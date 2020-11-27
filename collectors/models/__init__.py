"""Models for data returned by collectors. All models are expected to be initialized
with correct values for non-default fields; for example, a team's final rank
must be known at object creation and is not computed over time by calling object methods. Fields
with default values may be, and are expected to be, modified after initialization.

Data is sometimes duplicated between branches. The same Player may be found in both Roster
and Draft objects. There are a couple reasons for this.
    1. This is intended to facilitate dumping data to JSON in a way that the consumer
       can get all the data it needs with minimal querying.
    2. This makes populating the object easier. The objects can be populated with data
       directly after retrieval instead of having to query for the correct "foreign keys".
"""

from collectors.models.base import CamelCasedDataclass
from collectors.models.league import League
from collectors.models.manager import Manager
from collectors.models.player import Player
from collectors.models.record import Record
from collectors.models.roster import Roster
from collectors.models.season import Season
from collectors.models.week import Week
