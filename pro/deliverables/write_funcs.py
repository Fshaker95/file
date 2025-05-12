"""write_funcs.py
This file contains all of the write functionality needed to operate and maintain the board-game club's database. This
file addresses all of the write events included in kva2_design.pdf.

Please only import the following in your scripts:

- `add_player`
- `add_schedule`
- `add_game_record`

Every function starting with a double underscore "__" is considered a helper/internal function and is only used to
compose `add_player`, `add_schedule`, and `add_game_record` into smaller, well-defined functions.
"""

import json
import uuid
from typing import List, Tuple, Union
from typing_extensions import Literal

from redis import Redis

import keys
from models import BoardGameClubNotUniqueError, GameRecordTypedDict, PlayerTypedDict, ScheduleTypedDict


def add_player(redis_client: Redis, player: PlayerTypedDict) -> None:
    """Handles all redis reads/writes when adding a new player to the database
    In kva2_design.pdf, this function will be used for handling the "E2: when a new player is added" write event
    """
    __assert_player_is_new(redis_client, player["user_id"])

    ### init player keys
    pid = player["user_id"]
    redis_client.mset({
        keys.PLAYER_EMAIL.format(pid=pid): player["email"],
        keys.PLAYER_WINS.format(pid=pid): 0,
        keys.PLAYER_LOSSES.format(pid=pid): 0,
        keys.PLAYER_DRAWS.format(pid=pid): 0,
        keys.PLAYER_MOST_FREQ_OPENING_COUNT.format(pid=pid): 0,
    })

    ### update global keys
    redis_client.sadd(keys.GLOBAL_PLAYERS_EMAILS, player["email"])


def __assert_player_is_new(redis_client: Redis, pid: str) -> None:
    """Enforces `pid` uniqueness by checking `pid` against the global `pid` set
    NOTE: only use when adding a new player
    """
    added = redis_client.sadd(keys.GLOBAL_PLAYERS_IDS, pid)
    if added == 0:
        raise BoardGameClubNotUniqueError(f"user_id {pid} is already taken")


def add_schedule(redis_client: Redis, schedule: ScheduleTypedDict) -> None:
    """Handles all redis reads/writes when adding a new scheduled game to the database
    In kva2_design.pdf, this function will be used for handling the "E3: when a new game is scheduled" write event
    """
    __assert_game_is_new(redis_client, schedule["game_id"])

    ### player-specific keys
    player_1_key = keys.PLAYER_SCHEDULED_GAME_OPPONENT.format(pid=schedule['player_1'], gid=schedule['game_id'])
    player_2_key = keys.PLAYER_SCHEDULED_GAME_OPPONENT.format(pid=schedule['player_2'], gid=schedule['game_id'])
    redis_client.mset({
        player_1_key: schedule["player_2"],
        player_2_key: schedule["player_1"],
    })

    # set key to expire in the next 259200 seconds (= 72 hours)
    redis_client.expire(player_1_key, 259200)
    redis_client.expire(player_2_key, 259200)

    # per-player index (max 200 entries for every 72 hours)
    p1_list = keys.PLAYER_SCHEDULED_GAMES.format(pid=schedule['player_1'])
    p2_list = keys.PLAYER_SCHEDULED_GAMES.format(pid=schedule['player_2'])

    redis_client.lpush(p1_list, schedule["game_id"])
    redis_client.ltrim(p1_list, 0, 199)

    redis_client.lpush(p2_list, schedule["game_id"])
    redis_client.ltrim(p2_list, 0, 199)


def __new_fid(redis_client: Redis) -> str:
    """Returns a UUID that is not already a friend group (i.e., `fid`) key"""
    while True:
        fid = uuid.uuid4().hex
        if not redis_client.exists(keys.GLOBAL_FRIEND_GROUP.format(fid=fid)):
            return fid


def __update_friend_groups(redis_client: Redis, pid1: str, pid2: str) -> None:
    """Updates the friend group data structures when a new game record is added to the database"""
    fid1 = redis_client.get(keys.PLAYER_FRIEND_GROUP.format(pid=pid1))
    fid2 = redis_client.get(keys.PLAYER_FRIEND_GROUP.format(pid=pid2))

    # Case 1: neither in a group -> create new
    if fid1 is None and fid2 is None:
        gid = __new_fid(redis_client)
        pipe = redis_client.pipeline()
        pipe.sadd(keys.GLOBAL_FRIEND_GROUP.format(fid=gid), pid1, pid2)
        pipe.mset({
            keys.PLAYER_FRIEND_GROUP.format(pid=pid1): gid,
            keys.PLAYER_FRIEND_GROUP.format(pid=pid2): gid,
        })
        pipe.execute()
        return

    # Case 2: one of them in a group -> add the other one to it
    if fid1 is None or fid2 is None:
        gid = fid1 or fid2
        newcomer = pid2 if fid1 else pid1
        pipe = redis_client.pipeline()
        pipe.sadd(keys.GLOBAL_FRIEND_GROUP.format(fid=gid), newcomer)
        pipe.set(keys.PLAYER_FRIEND_GROUP.format(pid=newcomer), gid)
        pipe.execute()
        return

    # Case 3: both already in the same group -> nothing to do
    if fid1 == fid2:
        return

    # Case 4: different groups -> merge smaller into larger
    size1 = redis_client.scard(keys.GLOBAL_FRIEND_GROUP.format(fid=fid1))
    size2 = redis_client.scard(keys.GLOBAL_FRIEND_GROUP.format(fid=fid2))
    big, small = (fid1, fid2) if size1 >= size2 else (fid2, fid1)

    members = redis_client.smembers(keys.GLOBAL_FRIEND_GROUP.format(fid=small))
    if members:
        pipe = redis_client.pipeline()
        pipe.sadd(keys.GLOBAL_FRIEND_GROUP.format(fid=big), *members)
        for m in members:
            pipe.set(keys.PLAYER_FRIEND_GROUP.format(pid=m), big)
        pipe.delete(keys.GLOBAL_FRIEND_GROUP.format(fid=small))
        pipe.execute()


def __find_number_of_checks(moves: List[str]) -> int:
    """Finds the total number of checks in the given moveset"""
    number_of_checks = 0
    for move in moves:
        if move.find("+") >= 0:
            number_of_checks += 1
    return number_of_checks


def __parse_moveset(moveset: Union[str, List[str]]) -> List[str]:
    """Parses `moveset` as a Python list"""
    if isinstance(moveset, list):
        return moveset
    else:
        # NOTE: replacing ' with " to conform to JSON syntax requirements
        # NOTE: avoided using `eval` in case of potential injection attacks through the CSV file
        return json.loads(moveset.replace("'", '"'))


def __find_all_three_move_sequences(moves: List[str]) -> List[str]:
    """Identifies all three-move sequences made in the given moveset, where each sequence is represented as a
    comma-separated string (e.g., "d4,d5,c4")
    """
    return [
        # moves[i-2]     : the 1st move in the three-move sequence
        # moves[i-1]     : the 2nd move in the three-move sequence
        # moves[i]       : the 3rd move in the three-move sequence
        # moves[i-2:i+1] : the three-move sequence where the inclusive start is i-2 and the exclusive end is i+1
        ",".join(moves[i - 2 : i + 1])
        for i in range(2, len(moves))
    ]


def __update_player_keys(
        redis_client: Redis,
        game_record: GameRecordTypedDict,
        player_color: Literal["white", "black"],
        player_id: str,
        opponent_color: Literal["white", "black"],
        opponent_id: str) -> None:
    """Handles updating player-specific keys when adding a new game record"""

    if game_record["winner"] == player_color:
        wins = redis_client.incr(keys.PLAYER_WINS.format(pid=player_id), 1)
        __update_top_list(redis_client, keys.ANALYTICS_TOP_WINS, player_id, wins)
    elif game_record["winner"] == opponent_color:
        losses = redis_client.incr(keys.PLAYER_LOSSES.format(pid=player_id), 1)
        __update_top_list(redis_client, keys.ANALYTICS_TOP_LOSSES, player_id, losses)
    else:
        redis_client.incr(keys.PLAYER_DRAWS.format(pid=player_id), 1)
    redis_client.rpush(keys.PLAYER_GAMES_LIST.format(pid=player_id), game_record["game_id"])
    redis_client.sadd(keys.PLAYER_GAMES_SET.format(pid=player_id), game_record["game_id"])
    redis_client.sadd(keys.PLAYER_OPPONENTS.format(pid=player_id), opponent_id)
    # NOTE: based on the 365Chess dataset (https://www.365chess.com/eco.php), it seems that openings are counted for
    # both the White and Black players, regardless of whether the opening is a single-move opening (involving only
    # the White player) or a multi-move opening (involving both players)
    this_game_eco_count = redis_client.incr(keys.PLAYER_OPENING_COUNT.format(pid=player_id, eco=game_record['opening_eco']), 1)
    # determine if this game's opening is now the player's most frequently used opening
    most_used_eco_count = redis_client.get(keys.PLAYER_MOST_FREQ_OPENING_COUNT.format(pid=player_id))
    if most_used_eco_count is None or this_game_eco_count > int(most_used_eco_count):
        redis_client.mset({
            keys.PLAYER_MOST_FREQ_OPENING.format(pid=player_id): game_record["opening_eco"],
            keys.PLAYER_MOST_FREQ_OPENING_COUNT.format(pid=player_id): this_game_eco_count,
        })


def add_game_record(redis_client: Redis, game_record: GameRecordTypedDict) -> None:
    """Handles all redis reads/writes when adding a new game record to the database
    In kva2_design.pdf, this function will be used for handling the "E4: when a game record is inserted" write event
    """
    __assert_game_is_new(redis_client, game_record["game_id"])

    moves = __parse_moveset(game_record["moveset"])
    three_move_sequences = __find_all_three_move_sequences(moves)

    # add all 3-seq to the global set
    for seq in three_move_sequences:
        redis_client.sadd(keys.GLOBAL_SEQ_GAMES.format(seq=seq), game_record["game_id"])

    __update_player_keys(
        redis_client,
        game_record,
        player_color="white",
        player_id=game_record["white_player_id"],
        opponent_color="black",
        opponent_id=game_record["black_player_id"])
    __update_player_keys(
        redis_client,
        game_record,
        player_color="black",
        player_id=game_record["black_player_id"],
        opponent_color="white",
        opponent_id=game_record["white_player_id"])

    ### game-specific keys
    __update_game_keys(redis_client, game_record, moves)

    ### global keys
    __update_common_seqs(redis_client, three_move_sequences)
    this_game_eco_count = redis_client.incr(keys.GLOBAL_OPENING_COUNT.format(eco=game_record['opening_eco']), 1)

    ### analytics keys
    __update_shortest_game(redis_client, game_record)
    __update_most_freq_opening(redis_client, game_record, this_game_eco_count)
    __update_friend_groups(redis_client, game_record["white_player_id"], game_record["black_player_id"])


def __update_top_list(redis_client: Redis, list_key: str, pid: str, new_score: int) -> None:
    """Keeps `list_key` (descending tuples of 'pid:score') in sync with a max length of 10
    NOTE: must be called right **AFTER** you increment the underlying counter
    """
    old_tuple = f"{pid}:{new_score - 1}"
    new_tuple = f"{pid}:{new_score}"

    # atomically
    with redis_client.pipeline() as pipe:
        pipe.lrem(list_key, 0, old_tuple)  # remove stale record
        pipe.lrange(list_key, 0, -1)  # read the current list
        top = pipe.execute()[1]

        # find insert position
        insert_before = None
        for item in top:
            _, score = item.split(":")
            if new_score >= int(score):
                insert_before = item
                break

        # insert
        if insert_before is None:
            pipe.rpush(list_key, new_tuple)  # smallest → append
        else:
            pipe.linsert(list_key, "BEFORE", insert_before, new_tuple)

        # trim if we now have 11 items
        pipe.ltrim(list_key, 0, 9)
        pipe.execute()


def __assert_game_is_new(redis_client: Redis, gid: str) -> None:
    """Enforces `gid` uniqueness by checking `gid` against the global `gid` set
    NOTE: only use when adding a new game
    """
    added = redis_client.sadd(keys.GLOBAL_GAMES_IDS, gid)
    if added == 0:
        raise BoardGameClubNotUniqueError(f"game_id {gid} is already taken")


def __update_game_keys(redis_client: Redis, game_record: GameRecordTypedDict, moves: List[str]) -> None:
    """Handles updating game-specific keys when adding a new game record"""
    gid = game_record['game_id']
    redis_client.mset({
        keys.GAME_WINNER.format(gid=gid): game_record["winner"],
        keys.GAME_VICTORY_STATUS.format(gid=gid): game_record["victory_status"],
        keys.GAME_TURNS.format(gid=gid): game_record["number_of_turns"],
        keys.GAME_CHECKS.format(gid=gid): __find_number_of_checks(moves),
        keys.GAME_WHITE_PLAYER.format(gid=gid): game_record["white_player_id"],
        keys.GAME_BLACK_PLAYER.format(gid=gid): game_record["black_player_id"],
        keys.GAME_OPENING_ECO.format(gid=gid): game_record["opening_eco"],
    })
    redis_client.rpush(keys.GAME_MOVES.format(gid=gid), *moves)


def __update_common_seqs(redis_client: Redis, three_move_sequences: List[str]) -> None:
    """Updates the keys for determining the least/most common three-move sequences"""
    for three_move_sequence in three_move_sequences:
        new_count = redis_client.incr(keys.GLOBAL_SEQ_COUNT.format(seq=three_move_sequence), 1)
        __update_most_common_seqs(redis_client, three_move_sequence, new_count)
        __update_least_common_seqs(redis_client, three_move_sequence, new_count)


def __update_most_freq_opening(redis_client: Redis, game_record: GameRecordTypedDict, this_game_eco_count: str) -> None:
    """Determines if the opening in the given `game_record` now beats the current most frequently used opening across
    all games; if so, the appropriate keys are updated
    """
    most_used_eco_count = redis_client.get(keys.ANALYTICS_MOST_FREQ_OPENING_COUNT)
    if most_used_eco_count is None or this_game_eco_count > int(most_used_eco_count):
        redis_client.mset({
            keys.ANALYTICS_MOST_FREQ_OPENING: game_record["opening_eco"],
            keys.ANALYTICS_MOST_FREQ_OPENING_COUNT: this_game_eco_count,
        })


def __update_shortest_game(redis_client: Redis, game_record: GameRecordTypedDict) -> None:
    """Determines if the turns in the given `game_record` now beats the current shortest game; if so, the appropriate
    keys are updated
    """
    current_shortest_game_turns = redis_client.get(keys.ANALYTICS_SHORTEST_GAME_TURNS)
    if current_shortest_game_turns is None or int(game_record["number_of_turns"]) < int(current_shortest_game_turns):
        redis_client.mset({
            keys.ANALYTICS_SHORTEST_GAME: game_record["game_id"],
            keys.ANALYTICS_SHORTEST_GAME_TURNS: game_record["number_of_turns"],
        })


def __update_least_common_seqs(redis_client: Redis, three_move_sequence: str, new_count: int) -> None:
    """Determines if the given `three_move_sequence` now beats the current least common sequence; if so, the appropriate
    keys are updated
    """
    least_count = redis_client.get(keys.ANALYTICS_LEAST_COMMON_SEQ_COUNT)
    least_count = int(least_count) if least_count is not None else None

    # fresh DB OR new global minimum
    if least_count is None or new_count < least_count:
        pipe = redis_client.pipeline()
        pipe.delete(keys.ANALYTICS_LEAST_COMMON_SEQS)
        pipe.sadd(keys.ANALYTICS_LEAST_COMMON_SEQS, three_move_sequence)
        pipe.set(keys.ANALYTICS_LEAST_COMMON_SEQ_COUNT, new_count)
        pipe.execute()

    # exact tie with current minimum
    elif new_count == least_count:
        redis_client.sadd(keys.ANALYTICS_LEAST_COMMON_SEQS, three_move_sequence)

    # sequence lost “least” status
    elif new_count > least_count and redis_client.sismember(keys.ANALYTICS_LEAST_COMMON_SEQS, three_move_sequence):
        pipe = redis_client.pipeline()
        pipe.srem(keys.ANALYTICS_LEAST_COMMON_SEQS, three_move_sequence)
        pipe.scard(keys.ANALYTICS_LEAST_COMMON_SEQS)
        remaining = pipe.execute()[1]

        if remaining == 0:
            # We lost the last least-common sequence -> find the new minimum.
            new_min_count, new_min_seqs = __find_least_common_seqs(redis_client)
            if new_min_seqs:
                pipe = redis_client.pipeline()
                pipe.delete(keys.ANALYTICS_LEAST_COMMON_SEQS)
                pipe.sadd(keys.ANALYTICS_LEAST_COMMON_SEQS, *new_min_seqs)
                pipe.set(keys.ANALYTICS_LEAST_COMMON_SEQ_COUNT, new_min_count)
                pipe.execute()


def __find_least_common_seqs(redis_client: Redis) -> Tuple[int, List[str]]:
    """If __update_least_common_seqs determines that the current least common sequence has lost its position, this
    helper function determines the next least common sequence
    """
    min_count = None
    min_seqs = []
    for key in redis_client.scan_iter(keys.GLOBAL_SEQ_COUNT.format(seq="*")):
        cnt = int(redis_client.get(key))
        if cnt and (min_count is None or cnt < min_count):
            min_count = cnt
            # Extract the sequence from the key
            seq = key[len(keys.GLOBAL_SEQ_PREFIX):-6]
            min_seqs = [seq]
        elif cnt == min_count:
            seq = key[len(keys.GLOBAL_SEQ_PREFIX):-6]
            min_seqs.append(seq)
    return min_count, min_seqs


def __update_most_common_seqs(redis_client: Redis, three_move_sequence: str, new_count: int) -> None:
    """Determines if the given `three_move_sequence` now beats the current most common sequence; if so, the appropriate
    keys are updated
    """
    # Check the most common sequence
    most_count = redis_client.get(keys.ANALYTICS_MOST_COMMON_SEQ_COUNT)
    most_count = int(most_count) if most_count is not None else None
    if most_count is None or new_count > most_count:
        # new max -> replace the whole Set
        pipe = redis_client.pipeline()
        pipe.delete(keys.ANALYTICS_MOST_COMMON_SEQS)
        pipe.sadd(keys.ANALYTICS_MOST_COMMON_SEQS, three_move_sequence)
        pipe.set(keys.ANALYTICS_MOST_COMMON_SEQ_COUNT, new_count)
        pipe.execute()
    elif new_count == most_count:
        # tie with the current max -> add it to the Set
        redis_client.sadd(keys.ANALYTICS_MOST_COMMON_SEQS, three_move_sequence)
