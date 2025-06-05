import sqlite3
import requests
import os
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sleeper_players.db")
DB_PATH = os.path.abspath(DB_PATH)
PLAYER_API_URL = "https://api.sleeper.app/v1/players/nfl"
REFRESH_INTERVAL = 7 * 24 * 60 * 60  # 7 days in seconds
RELEVANT_POSITIONS = {"QB", "WR", "RB", "TE", "K"}


#Check the last modified time of the DB file to decide if we should update.
def should_refresh_data():
    if not os.path.exists(DB_PATH):
        return True
    last_modified = os.path.getmtime(DB_PATH)
    return time.time() - last_modified > REFRESH_INTERVAL

def fetch_and_store_players():
    print("Fetching player data from Sleeper...")
    print("Loading into " + DB_PATH)
    res = requests.get(PLAYER_API_URL)
    if res.status_code != 200:
        raise Exception("Failed to fetch player data")

    players = res.json()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM players")  # wipe old data

    count = 0
    for player_id, data in players.items():
        if data.get("position") not in RELEVANT_POSITIONS:
            continue

        values = (
            player_id,
            data.get("first_name"),
            data.get("last_name"),
            data.get("height"),
            data.get("weight"),
            data.get("number"),
            data.get("position"),
            data.get("team"),
            data.get("college"),
            data.get("status"),
            data.get("injury_status"),
            data.get("age"),
            data.get("years_exp"),
        )
        cursor.execute("""
            INSERT INTO players (
                player_id, first_name, last_name, height, weight,
                number, position, team, college, status,
                injury_status, age, years_exp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        count += 1

    conn.commit()
    conn.close()
    print(f"Inserted {count} players into the database.")

if __name__ == "__main__":
    if should_refresh_data():
        fetch_and_store_players()
        print("Player data updated successfully.")
    else:
        print("Player data is up-to-date; skipping fetch.")
