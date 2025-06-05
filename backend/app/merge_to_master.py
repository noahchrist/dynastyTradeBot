import sqlite3

# --- Connect to databases ---
sleeper_conn = sqlite3.connect("./data/sleeper_players.db")
fc_conn = sqlite3.connect("./data/fantasycalc_rankings.db")
master_conn = sqlite3.connect("./data/master.db")

sleeper_cursor = sleeper_conn.cursor()
fc_cursor = fc_conn.cursor()
master_cursor = master_conn.cursor()

# --- Load Sleeper players into a lookup dictionary ---
sleeper_cursor.execute("""
    SELECT player_id, first_name, last_name, team, position, age, years_exp
    FROM players
""")
sleeper_players = {}
for row in sleeper_cursor.fetchall():
    full_name = f"{row[1]} {row[2]}"
    sleeper_players[full_name] = {
        "player_id": row[0],
        "team": row[3],
        "position": row[4],
        "age": row[5],
        "years_exp": row[6]
    }

# --- Load FantasyCalc rankings ---
fc_cursor.execute("SELECT player_name, value FROM rankings")
fc_players = fc_cursor.fetchall()

# --- Prepare master insert ---
master_cursor.execute("DELETE FROM master")  # Clear old data

row_count = 0
for name, value in fc_players:
    # Handle special case
    lookup_name = "Marvin Harrison" if name == "Marvin Harrison Jr" else name

    sleeper_data = sleeper_players.get(lookup_name)
    if sleeper_data:
        master_cursor.execute("""
            INSERT INTO master (
                player_id, team_id, name, team, position, age, years_exp, value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sleeper_data["player_id"],
            None,  # team_id will be filled later
            name,  # use FantasyCalc's display name
            sleeper_data["team"],
            sleeper_data["position"],
            sleeper_data["age"],
            sleeper_data["years_exp"],
            value
        ))
        row_count += 1

# --- Commit and close ---
master_conn.commit()
sleeper_conn.close()
fc_conn.close()
master_conn.close()

print(f"added {row_count} rows to the master table")
