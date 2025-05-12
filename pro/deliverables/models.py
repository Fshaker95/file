"""models.py
Defines `TypedDict` classes used to represent player, schedule, and game record data. These classes are used for
defining Python type hints (used by IDEs and code editors), not for defining runtime constraints. In addition to these
classes, custom exceptions are also defined to help distinguish domain-specific errors from other errors.
"""

from typing import List, Union
from typing_extensions import Literal, TypedDict


class PlayerTypedDict(TypedDict):
    """Python typed dictionary representing a row in the `players.csv` dataset"""
    user_id: str
    email: str


class ScheduleTypedDict(TypedDict):
    """Python typed dictionary representing a row in the `schedule.csv` dataset"""
    game_id: str
    player_1: str
    player_2: str


class GameRecordTypedDict(TypedDict):
    """Python typed dictionary representing a row in the `game_records.csv` dataset"""
    game_id: str
    moveset: Union[str, List[str]]
    winner: Literal["white", "black", "draw"]
    victory_status: str
    number_of_turns: Union[str, int]
    white_player_id: str
    black_player_id: str
    opening_eco: str


# Custom Exceptions


class BoardGameClubRootError(Exception):
    """The root exception class if attempting to catch any error raised by the board-game club's application logic"""

class BoardGameClubLoadTransformError(BoardGameClubRootError):
    """Custom exception class to denote errors specific to `load_transform.py`"""

class BoardGameClubWriteError(BoardGameClubRootError):
    """Custom exception class to denote errors occurring during write events"""

class BoardGameClubNotUniqueError(BoardGameClubWriteError):
    """Custom exception class: the user attempted to create an entity using an existing identifier"""
