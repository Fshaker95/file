from redis import Redis
import keys
import json

# Connect to Redis
r = Redis(host='localhost', port=6379, decode_responses=True)

# --- Analytics Functions ---

def get_shortest_game():
    game_id = r.get(keys.ANALYTICS_SHORTEST_GAME)
    num_turns = r.get(keys.ANALYTICS_SHORTEST_GAME_TURNS)
    return {"game_id": game_id, "number_of_turns": int(num_turns) if num_turns else None}

def get_check_counts():
    keys_list = r.keys("game:*:number_of_checks")
    return {key.split(":")[1]: int(r.get(key)) for key in keys_list}

def get_most_frequent_opening():
    opening = r.get(keys.ANALYTICS_MOST_FREQ_OPENING)
    count = r.get(keys.ANALYTICS_MOST_FREQ_OPENING_COUNT)
    return {"opening_eco": opening, "count": int(count) if count else 0}

def get_most_common_3move_sequence():
    sequences = r.smembers(keys.ANALYTICS_MOST_COMMON_SEQS)
    count = r.get(keys.ANALYTICS_MOST_COMMON_SEQ_COUNT)
    return {"sequences": list(sequences), "count": int(count) if count else 0}

def get_least_common_3move_sequence():
    sequences = r.smembers(keys.ANALYTICS_LEAST_COMMON_SEQS)
    count = r.get(keys.ANALYTICS_LEAST_COMMON_SEQ_COUNT)
    return {"sequences": list(sequences), "count": int(count) if count else 0}

# --- print output ---

if __name__ == "__main__":
        # Shortest Game
        print("------------------------------------------\nShortest Game:\n")
        shortest = get_shortest_game()
        print(shortest["game_id"] + "\n\n")

        # Check Counts (all games)
        print("------------------------------------------\nCheck Counts (all games):\n")
        checks = get_check_counts()
        for game_id, count in sorted(checks.items()):
            print(f"{game_id}: {count}\n")
        print("\n")

        # Most Frequent Opening
        print("------------------------------------------\nMost Frequent Opening:\n")
        opening = get_most_frequent_opening()
        print(opening["opening_eco"] + "\n\n")

        # Most Common 3-Move Sequences
        print("------------------------------------------\nMost Common 3-Move Sequences:\n")
        common = get_most_common_3move_sequence()
        print(f"Used: {common['count']}\n")
        print("Sequences:\n")
        for seq in common['sequences'][:5]:
            print(f"- {seq}\n")
        print("\n")

        # Least Common 3-Move Sequences
        print("------------------------------------------\nLeast Common 3-Move Sequences:\n")
        least = get_least_common_3move_sequence()
        print(f"Used: {least['count']}\n")
        print("Sequences:\n")
        for seq in least['sequences'][:5]:
            print(f"- {seq}\n")



        """
        # --- Output to File ---

if __name__ == "__main__":
    with open("analytics_output.txt", "w", encoding="utf-8") as f:
        # Shortest Game
        f.write("------------------------------------------\nShortest Game:\n")
        shortest = get_shortest_game()
        f.write(shortest["game_id"] + "\n\n")

        # Check Counts (all games)
        f.write("------------------------------------------\nCheck Counts (all games):\n")
        checks = get_check_counts()
        for game_id, count in sorted(checks.items()):
            f.write(f"{game_id}: {count}\n")
        f.write("\n")

        # Most Frequent Opening
        f.write("------------------------------------------\nMost Frequent Opening:\n")
        opening = get_most_frequent_opening()
        f.write(opening["opening_eco"] + "\n\n")

        # Most Common 3-Move Sequences
        f.write("------------------------------------------\nMost Common 3-Move Sequences:\n")
        common = get_most_common_3move_sequence()
        f.write(f"Used: {common['count']}\n")
        f.write("Sequences:\n")
        for seq in common['sequences'][:5]:
            f.write(f"- {seq}\n")
        f.write("\n")

        # Least Common 3-Move Sequences
        f.write("------------------------------------------\nLeast Common 3-Move Sequences:\n")
        least = get_least_common_3move_sequence()
        f.write(f"Used: {least['count']}\n")
        f.write("Sequences:\n")
        for seq in least['sequences'][:5]:
            f.write(f"- {seq}\n")
"""
