"""graph_funcs.py
This file contains all of the read functionalities needed to satisfy the board-game club's Graph query requirements. To
demonstrate these functionalities, this file may be invoked as a Python script to run example queries.
"""

from typing import List

from redis import Redis

import keys


def get_friends_of_friends(r: Redis, pid: str) -> List[str]:
    """Requirement: List the “friends of friends” of an arbitrary player (P0). Here, ”friends” refers to all opponents
    a given player has had.

    This query defines "friends of friends" as Player P0's opponents' opponents, meaning any of Player P0's direct
    opponents are excluded from the returned set.
    """
    fid = r.get(keys.PLAYER_FRIEND_GROUP.format(pid=pid))
    if fid is None:
        return []

    fof_set = set(
        r.sdiff(keys.GLOBAL_FRIEND_GROUP.format(fid=fid), keys.PLAYER_OPPONENTS.format(pid=pid))
    )
    fof_set.discard(pid)
    return list(fof_set)


def get_filtered_friends_of_friends(r: Redis, pid: str) -> List[str]:
    """Requirement: Filter the “friends of friends” query above to return only those players who have a higher total
    number of wins than P0.
    """
    fof_list = get_friends_of_friends(r, pid)
    if not fof_list:
        return []

    player_wins = int(r.get(keys.PLAYER_WINS.format(pid=pid)) or 0)

    pipe = r.pipeline()
    for fof_pid in fof_list:
        pipe.get(keys.PLAYER_WINS.format(pid=fof_pid))
    fof_wins = [int(number_of_wins or 0) for number_of_wins in pipe.execute()]

    return [
        fof_pid
        for fof_pid, number_of_wins in zip(fof_list, fof_wins)
        if number_of_wins > player_wins
    ]


def get_longest_connected_component() -> List[str]:
    """Requirement: For a graph where all vertices are players, and an edge exists between two verticies if the players
    have played a game against each other, what is the longest connected component?
    """
    raise NotImplementedError()


if __name__ == "__main__":
    redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=True)

    print("Friends of Friends Query Demonstration")
    print()

    pid = "xandersky"
    print(f"Friends of Friends (FoF) information for player '{pid}':")
    fof = get_friends_of_friends(redis_client, pid)
    print(f"FoF: {fof}")
    filtered_fof = get_filtered_friends_of_friends(redis_client, pid)
    print(f"Filtered FoF: {filtered_fof}")
    print()

    pid = "smilsydov"
    print(f"Friends of Friends (FoF) information for player '{pid}':")
    fof = get_friends_of_friends(redis_client, pid)
    print(f"FoF: (set of {len(fof)} players)")
    filtered_fof = get_filtered_friends_of_friends(redis_client, pid)
    print(f"Filtered FoF: {filtered_fof}")
    print()

    print("Longest Connected Component:")
    longest_connected_component = get_longest_connected_component()
    print(longest_connected_component)
