"""load_transform.py
Script used to bootstrap the board-game club's redis database with their current CSV datasets. Bootstrapping aligns with
the group's strategies and designs as outlined in kva2_design.pdf. Before running the script, the CSV datasets are
expected to be in the (root directory)/csv_files/ directory and to conform to the schemas below. All CSV datasets must
include a header row, with the attributes below as the headers, as the first row.

Expected Directory Tree:
.
├── csv_files/
│   ├── players.csv
│   ├── schedule.csv
│   └── game_records.csv
└── deliverables/
    └── load_transform.py

Expected `players.csv` Schema:
| Attribute | Data Type | Description                         |
| --------- | --------- | ----------------------------------- |
| user_id   | String    | An ID uniquely identifying a player |
| email     | String    | The email address of a player       |

Expected `schedule.csv` Schema:
| Attribute | Data Type | Description                                      |
| --------- | --------- | ------------------------------------------------ |
| game_id   | String    | An ID uniquely identifying the game to be played |
| player_1  | String    | The user_id of Player 1                          |
| player_2  | String    | The user_id of Player 2                          |

Expected `game_records.csv` Schema:
| Attribute       | Data Type    | Description                                                                   |
| --------------- | ------------ | ----------------------------------------------------------------------------- |
| game_id         | String       | The ID of this particular game                                                |
| moveset         | String Array | An array of moves each player made, in game order, in standard chess notation |
| winner          | String       | The player who won - Black, White, or Draw                                    |
| victory_status  | String       | The nature of the resolution of the game                                      |
| number_of_turns | Integer      | The number of turns the game lasted                                           |
| white_player_id | String       | The user_id of the player that was assigned the White pieces                  |
| black_player_id | String       | The user_id of the player that was assigned the Black pieces                  |
| opening_eco     | String       | A standardized code representing the opening moves                            |
"""

import csv
from pathlib import Path
from typing import Callable, Dict

from redis import Redis

from models import BoardGameClubLoadTransformError, BoardGameClubNotUniqueError, GameRecordTypedDict
from write_funcs import add_game_record, add_player, add_schedule


def create_path_obj(path_str: str) -> Path:
    """Creates a Path object, validating that the `path_str` parameter points to an existing file in csv_files/"""
    base_dir = Path(__file__).resolve().parent.parent  # one level up from deliverables/
    path_obj = base_dir / "csv_files" / path_str
    if not path_obj.exists():
        raise BoardGameClubLoadTransformError(f"{path_str} does not exist")
    if not path_obj.is_file():
        raise BoardGameClubLoadTransformError(f"{path_str} is not a file")
    if path_obj.suffix != ".csv":
        raise BoardGameClubLoadTransformError(f"{path_str} is not a CSV file")
    return path_obj


def process_csv_file(path: Path, func: Callable[[Dict[str, str]], None]) -> None:
    """Iterates through each row (excluding the header) and calls `func` for each row; `func` should expect a dictionary
    representation for each row, with keys representing the headers

    Example:
    process_csv_file(players_csv_path, lambda row: print(row))

    Output:
    {'user_id': 'a-00', 'email': 'a-00@gmail.com'}
    {'user_id': 'skinnerua', 'email': 'skinnerua@hotmail.com'}
    ...
    {'user_id': 'belcolt', 'email': 'belcolt@hotmail.com'}
    """
    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file)
        header_row: list[str] = []
        for row in csv_reader:
            if len(header_row) == 0:
                header_row = row
            else:
                func(dict(zip(header_row, row)))


if __name__ == "__main__":
    players_csv_path = create_path_obj("players.csv")
    schedule_csv_path = create_path_obj("schedule.csv")
    game_records_csv_path = create_path_obj("game_records.csv")

    redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=True)
    # decode_responses is set to True so that bytes are automatically converted to str
    try:
        redis_client.ping()
        print("connection to redis successful: initial PING succeeded")
    except Exception as e:
        raise BoardGameClubLoadTransformError("no connection to redis: initial PING failed") from e

    process_csv_file(players_csv_path, lambda row: add_player(redis_client, row))
    print(f"completed processing {players_csv_path.name}")

    process_csv_file(schedule_csv_path, lambda row: add_schedule(redis_client, row))
    print(f"completed processing {schedule_csv_path.name}")

    def process_game_records_csv(row: GameRecordTypedDict) -> None:
        """Composes more complex behavior for the process_csv_file call for game_records.csv"""
        try:
            add_game_record(redis_client, row)
        except BoardGameClubNotUniqueError:
            # duplicate rows will be ignored since the duplicate game_ids seem to relate to the same exact information
            # print(f"DUPLICATE: {row['game_id']}")
            pass

    process_csv_file(game_records_csv_path, lambda row: process_game_records_csv(row))
    print(f"completed processing {game_records_csv_path.name}")
