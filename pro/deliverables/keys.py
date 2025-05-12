"""keys.py
This file provides global constant strings of all the available Redis keys. Please do not modify this file unless there
has been a change to the database schema/design.

Parameterized Keys
Applies to all keys containing "{pid}", "{fid}", "{gid}", "{eco}", or "{seq}". To use these keys, use the Python
`str` function `.format` to substitute the parameters for concrete values.

    Example: `PLAYER_EMAIL.format(pid='example-pid')`
"""

# player
PLAYER_PREFIX                  = "player:{pid}"
PLAYER_EMAIL                   = PLAYER_PREFIX + ":email"
PLAYER_WINS                    = PLAYER_PREFIX + ":number_of_wins"
PLAYER_LOSSES                  = PLAYER_PREFIX + ":number_of_losses"
PLAYER_DRAWS                   = PLAYER_PREFIX + ":number_of_draws"
PLAYER_GAMES_LIST              = PLAYER_PREFIX + ":games-list"
PLAYER_GAMES_SET               = PLAYER_PREFIX + ":games-set"
PLAYER_OPPONENTS               = PLAYER_PREFIX + ":opponents"
PLAYER_OPENING_COUNT           = PLAYER_PREFIX + ":openings:{eco}:count"
PLAYER_MOST_FREQ_OPENING       = PLAYER_PREFIX + ":most_freq_opening"
PLAYER_MOST_FREQ_OPENING_COUNT = PLAYER_PREFIX + ":most_freq_opening:count"
PLAYER_FRIEND_GROUP            = PLAYER_PREFIX + ":friend_group"
PLAYER_SCHEDULED_GAMES         = PLAYER_PREFIX + ":scheduled_games"
PLAYER_SCHEDULED_GAME_OPPONENT = PLAYER_PREFIX + ":scheduled_games:{gid}:opponent"

# game
GAME_PREFIX          = "game:{gid}"
GAME_WINNER          = GAME_PREFIX + ":winner"
GAME_VICTORY_STATUS  = GAME_PREFIX + ":victory_status"
GAME_TURNS           = GAME_PREFIX + ":number_of_turns"
GAME_CHECKS          = GAME_PREFIX + ":number_of_checks"
GAME_WHITE_PLAYER    = GAME_PREFIX + ":white_player_id"
GAME_BLACK_PLAYER    = GAME_PREFIX + ":black_player_id"
GAME_OPENING_ECO     = GAME_PREFIX + ":opening_eco"
GAME_MOVES           = GAME_PREFIX + ":moves"

# global
GLOBAL_PREFIX         = "global"
GLOBAL_PLAYERS_EMAILS = GLOBAL_PREFIX + ":players:emails"
GLOBAL_PLAYERS_IDS    = GLOBAL_PREFIX + ":players:ids"
GLOBAL_GAMES_IDS      = GLOBAL_PREFIX + ":games:ids"
GLOBAL_FRIEND_GROUP   = GLOBAL_PREFIX + ":friend_group:{fid}"
GLOBAL_SEQ_PREFIX     = GLOBAL_PREFIX + ":seq:"
GLOBAL_SEQ_GAMES      = GLOBAL_SEQ_PREFIX + "{seq}:games"
GLOBAL_SEQ_COUNT      = GLOBAL_SEQ_PREFIX + "{seq}:count"
GLOBAL_OPENING_COUNT  = GLOBAL_PREFIX + ":openings:{eco}:count"

# analytics
ANALYTICS_PREFIX                  = "analytics"
ANALYTICS_TOP_WINS                = ANALYTICS_PREFIX + ":top_wins"
ANALYTICS_TOP_LOSSES              = ANALYTICS_PREFIX + ":top_losses"
ANALYTICS_MOST_FREQ_OPENING       = ANALYTICS_PREFIX + ":most_freq_opening"
ANALYTICS_MOST_FREQ_OPENING_COUNT = ANALYTICS_PREFIX + ":most_freq_opening:count"
ANALYTICS_SHORTEST_GAME           = ANALYTICS_PREFIX + ":shortest_game"
ANALYTICS_SHORTEST_GAME_TURNS     = ANALYTICS_PREFIX + ":shortest_game:number_of_turns"
ANALYTICS_LEAST_COMMON_SEQS       = ANALYTICS_PREFIX + ":least_common_seqs"
ANALYTICS_LEAST_COMMON_SEQ_COUNT  = ANALYTICS_PREFIX + ":least_common_seq:count"
ANALYTICS_MOST_COMMON_SEQS        = ANALYTICS_PREFIX + ":most_common_seqs"
ANALYTICS_MOST_COMMON_SEQ_COUNT   = ANALYTICS_PREFIX + ":most_common_seq:count"
