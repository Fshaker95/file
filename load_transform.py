"""
load_transform.py

Bootstraps Redis with data from CSVs: players, scheduled games, and completed games.

Expected files in ./csv_files/:
- players.csv
- schedule.csv
- game_records.csv
"""

import csv
from pathlib import Path
from typing import Callable, Dict

from redis import Redis
from write_funcs import add_game_record, add_schedule, add_player
from models import BoardGameClubLoadTransformError, GameRecordTypedDict


def create_path_obj(path_str: str) -> Path:
    base_dir = Path(__file__).resolve().parent.parent
    path_obj = base_dir / "csv_files" / path_str
    if not path_obj.exists() or not path_obj.is_file() or path_obj.suffix != ".csv":
        raise BoardGameClubLoadTransformError(f"{path_str} is invalid or missing")
    return path_obj


def process_csv_file(path: Path, func: Callable[[Dict[str, str]], None], label: str) -> None:
    with open(path) as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)
        success, skipped = 0, 0

        for i, row in enumerate(reader):
            try:
                func(dict(zip(header, row)))
                success += 1
            except BoardGameClubLoadTransformError:
                skipped += 1
            if (i + 1) % 500 == 0:
                print(f"{label}: Processed {i+1} records...")

        print(f"{label}: ✅ {success} loaded, ❌ {skipped} skipped.")


def process_game_records_csv(path: Path, redis_client: Redis):
    print("starting to process game_records.csv...")
    with open(path) as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)
        success, skipped = 0, 0

        for i, row in enumerate(reader):
            record = dict(zip(header, row))
            try:
                add_game_record(redis_client, record)
                success += 1
            except BoardGameClubLoadTransformError:
                skipped += 1
            if (i + 1) % 500 == 0:
                print(f"game_records.csv: Processed {i+1} records...")

        print(f"game_records.csv: ✅ {success} loaded, ❌ {skipped} skipped.")


if __name__ == "__main__":
    players_csv_path = create_path_obj("players.csv")
    schedule_csv_path = create_path_obj("schedule.csv")
    game_records_csv_path = create_path_obj("game_records.csv")

    redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=True)

    try:
        redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        raise BoardGameClubLoadTransformError("❌ Redis connection failed") from e

    process_csv_file(players_csv_path, lambda row: add_player(redis_client, row), "players.csv")
    process_csv_file(schedule_csv_path, lambda row: add_schedule(redis_client, row), "schedule.csv")
    process_game_records_csv(game_records_csv_path, redis_client)
