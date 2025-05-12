#!/usr/bin/env python3
"""
Run functional smoke-tests against the chess-club Redis DB.

Each test is expressed in plain Redis terms so it doesn’t matter whether
you implemented helper functions or not.  Whenever the expected value is
unordered (a Set) the comparison ignores ordering; otherwise it expects
an exact match.
"""

from typing import Any, Sequence
from redis import Redis


##### helpers
def as_set(x: Any) -> set[str]:
    return set(x if isinstance(x, (list, tuple, set)) else [x])


def pretty(val: Any) -> str:
    return str(list(val) if isinstance(val, (set, list, tuple)) else val)


##### bind to Redis
redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)
try:
    redis.ping()
except Exception as e:
    raise SystemExit(f"Cannot reach Redis on localhost:6379 → {e}") from None


##### test catalogue
Test = dict[str, Any]  # loose alias for clarity

tests: Sequence[Test] = [
    # ── Player-centric ───────────────────────────────────────────
    {
        "desc": "match history for sureka_akshat",
        "cmd": lambda: redis.lrange("player:sureka_akshat:games-list", 0, -1),
        "exp": ["u7i6dOaJ", "guanvMR5", "PmpkWkmm", "EwaK0IsE",
                "ifUMWtVj", "gHld9WSr"],
        "setlike": False,
    },
    {
        "desc": "future games for evianwahter",
        "cmd": lambda: redis.lrange("player:evianwahter:scheduled_games", 0, -1),
        "exp": ["hiGJ4Tnd"],
        "setlike": False,
    },
    {
        "desc": "match history for evianwahter",
        "cmd": lambda: redis.lrange("player:evianwahter:games-list", 0, -1),
        "exp": ["c9WUjuhv", "KaOnp8yg", "pvqLRAqH"],
        "setlike": False,
    },
    {
        "desc": "email membership evianwahter@msn.com",
        "cmd": lambda: bool(redis.sismember("global:players:emails","evianwahter@msn.com")),
        "exp": True,
        "setlike": False,
    },
    {
        "desc": "games shivangithegenius vs rajuppi",
        "cmd": lambda: redis.sinter("player:shivangithegenius:games-set","player:rajuppi:games-set"),
        "exp": ["G5S21pXK", "oqoT4DLS", "tLnhk43J", "iq3Kz06t"],
        "setlike": True,
    },
    {
        "desc": "most-used opening for shivangithegenius",
        "cmd": lambda: redis.get("player:shivangithegenius:most_freq_opening"),
        "exp": "B21",
        "setlike": False,
    },

    # ── Leaderboards ─────────────────────────────────────────────
    {
        "desc": "top-10 wins list",
        "cmd": lambda: redis.lrange("analytics:top_wins", 0, -1),
        "exp": ["chesscarl:45", "doraemon61:38", "smilsydov:36", "unrim:33",
                "elvis1997:33", "brandonbos:33", "fabian1104:32",
                "lance5500:31", "youralterego:31", "apis11:31"],
        "setlike": False,
    },
    {
        "desc": "top-10 losses list",
        "cmd": lambda: redis.lrange("analytics:top_losses", 0, -1),
        "exp": ["nitsua49:39", "erikweisz:38", "fandm-lancaster:38",
                "pat222:37", "zapala:35", "marigw:35", "viswannabe:34",
                "derspiegel:34", "andreas00:34", "thebestofthebad:34"],
        "setlike": False,
    },

    # ── Game look-ups ────────────────────────────────────────────
    {
        "desc": "three-move seq e4,c5,Nf3 for player evianwahter",
        "cmd": lambda: redis.sinter("global:seq:e4,c5,Nf3:games","player:evianwahter:games-set"),
        "exp": ["c9WUjuhv", "pvqLRAqH"],
        "setlike": True,
    },
    {
        "desc": "global three-move seq Qxd6,Qe7,Bc5",
        "cmd": lambda: redis.smembers("global:seq:Qxd6,Qe7,Bc5:games"),
        "exp": ["c9WUjuhv", "e4TsEuRY"],
        "setlike": True,
    },

    # ── Analytics ────────────────────────────────────────────────
    {
        "desc": "shortest game id",
        "cmd": lambda: redis.get("analytics:shortest_game"),
        "exp": "3K5kYPO8",
        "setlike": False,
    },
    {
        "desc": "check count of game 0ehBTCJp",
        "cmd": lambda: redis.get("game:0ehBTCJp:number_of_checks"),
        "exp": "3",  # note: Redis returns str if decode_responses=True
        "setlike": False,
    },
    {
        "desc": "most frequent opening overall",
        "cmd": lambda: redis.get("analytics:most_freq_opening"),
        "exp": "A00",
        "setlike": False,
    },
    {
        "desc": "most common three-move sequence(s)",
        "cmd": lambda: redis.smembers("analytics:most_common_seqs"),
        "exp": ["e4,e5,Nf3"],
        "setlike": True,
    },
    {
        "desc": "least common three-move sequences (sample)",
        "cmd": lambda: redis.smembers("analytics:least_common_seqs"),
        "exp_subset": {"Kc7,Rh6,Nc4+", "a6,Bxf5,gxf5", "Qd2,Qe6,O-O-O", "Rd7,f4,Ra8", "Re6,Qe4+,g6"},
        "setlike": True,
        "subset": True,
    },
]


##### test-runner
def run(test: Test) -> bool:
    """Run one test, print outcome, and return True if it passed."""
    got = test["cmd"]()
    ok: bool
    if test.get("subset"):
        ok = test["exp_subset"].issubset(as_set(got))
    elif test["setlike"]:
        ok = as_set(got) == as_set(test["exp"])
    else:
        ok = got == test["exp"]

    status = "PASS" if ok else "FAIL"
    print(f"{status:4} — {test['desc']}")
    if not ok:
        print(f"      expected: {pretty(test.get('exp', test.get('exp_subset')))}")
        print(f"      got     : {pretty(got)}")
    return ok


if __name__ == "__main__":
    failures = sum(not run(t) for t in tests)
    if failures:
        print(f"\n{failures} test(s) FAILED")
        raise SystemExit(1)
    print("\nAll tests passed ✔")
