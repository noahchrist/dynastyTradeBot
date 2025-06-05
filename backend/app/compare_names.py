import sqlite3

# Connect to both databases
sleeper_conn = sqlite3.connect("./data/sleeper_players.db")
fantasycalc_conn = sqlite3.connect("./data/fantasycalc_rankings.db")

sleeper_cursor = sleeper_conn.cursor()
fantasycalc_cursor = fantasycalc_conn.cursor()

# Load all fantasycalc names
fantasycalc_cursor.execute("SELECT player_name FROM rankings")
fc_players = [row[0] for row in fantasycalc_cursor.fetchall()]

# Load all sleeper players with full name
sleeper_cursor.execute("SELECT first_name, last_name FROM players")
sleeper_players = set(f"{row[0]} {row[1]}" for row in sleeper_cursor.fetchall())

# Find unmatched fantasycalc players
print("\nUnmatched FantasyCalc Players:\n" + "-"*35)
for name in fc_players:
    if name not in sleeper_players:
        print(name)

# Clean up
sleeper_conn.close()
fantasycalc_conn.close()
