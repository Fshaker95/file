
## Tasks
| Task | Files delivered                                        | Depends on | Assignee |
| ---- | ------------------------------------------------------ | ---------- | -------- |
| T1   | • D1: `kva2_design.pdf` <br>• D2: `game_funcs.py`      | D2 → T2    | Shareef  |
| T2   | • D5: `load_transform.py`<br>• D7: `graph_funcs.py`    | T1         | Marc     |
| T3   | • D3: `player_funcs.py`<br>• D4:`leaderboard_funcs.py` | T1 + T2    | Abed     |
| T4   | • D6: `analytics_funcs.py`<br>• D8: `README.md`        | T1 + T2    | Fahad    |

## Timeline
- D1 by Mon 5th
- D5 by Wed 7th
- Rest by Sun 10th

# Deliverables

| #   | File / Doc             | What must be inside                                                                                                                                                                                                                                                         |
| --- | ---------------------- |-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| D1  | `kva2_design.pdf`      | • 3–4 pages<br>• Domain narrative <br>• Key table <br>• Read/write plan per requirement                                                                                                                                                                                     |
| D2  | `load_transform.py`    | • Read the three CSVs<br>• Create keys/values  shown in the key table<br>• Idempotent: if run twice DB state is identical                                                                                                                                                   |
| D3  | `player_funcs.py`      | • Six Player-Centric functions<br>    • `player_match_history(player_id)`<br>	• `future_games(player_id)`<br>	• `all_matches(player_id)`<br>	• `in_league(player_email)`<br>	• `games_against_opponent(player_id, opponent_id)`<br>	• `player_most_freq_opening(player_id)` |
| D4  | `leaderboard_funcs.py` | • Two Leaderboard functions  <br>    • `top_10()`<br>	• `bottom_10()`                                                                                                                                                                                                       |
| D5  | `game_funcs.py`        | • Three-move search (per-player & global)<br>    • `player_seq(user, seq)`<br>    • `global_seq(seq)`                                                                                                                                                                       |
| D6  | `analytics_funcs.py`   | • Five analytics queries using pre-aggregated keys<br>    • shortest game<br>	• check counts<br>	• `most_freq_opening()`<br>	• `most_common_three_moves()`<br>	• `least_common_three_moves`                                                                                 |
| D7  | `graph_funcs.py`       | • Three functions<br>	• `friends_of_friends(user)`<br>	• `filtered_friends_of_friends(user)`<br>	• `largest_connected_component()`                                                                                                                                          |
| D8  | `README.md`            | •  install + run instructions (needed for grading)`                                                                                                                                                                                                                         |

## Deliverable Examples
- `load_transform.py`
```python
def load_players(r, path): ...
def load_schedule(r, path): ...
def load_games(r, path): ...

if __name__ == "__main__":
    r = redis.Redis()
    load_players(r, "players.csv")
    load_schedule(r, "schedule.csv")
    load_games(r, "game_records.csv")
```
