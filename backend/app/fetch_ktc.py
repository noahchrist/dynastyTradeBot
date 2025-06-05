import requests
import sqlite3
from bs4 import BeautifulSoup
import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "ktc_rankings.db")
DB_PATH = os.path.abspath(DB_PATH)

# Ensure DB and table exist
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS rankings (
        player_name TEXT,
        value INTEGER
    )
""")
conn.commit()
conn.close()

# Scraping settings
BASE_URL = "https://keeptradecut.com/dynasty-rankings"
POSITION_FILTERS = "QB|WR|RB|TE|RDP"
FORMAT = 2

def scrape_ktc_rankings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rankings")  # clear old data

    total_inserted = 0
    headers = {"User-Agent": "Mozilla/5.0"}

    for page in range(10):  # Pages 0–9
        print(f"Scraping page {page + 1}...")
        url = f"{BASE_URL}?page={page}&filters={POSITION_FILTERS}&format={FORMAT}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        # Adjusted targeting based on updated site structure
        players = soup.select("div.onePlayer")

        for player in players:
            name_tag = player.select_one("div.player-name a")
            value_tag = player.select_one("div.value")

            if not name_tag or not value_tag:
                continue

            player_name = name_tag.text.strip()
            try:
                value = int(value_tag.text.strip())
            except ValueError:
                continue

            cursor.execute("""
                INSERT INTO rankings (player_name, value)
                VALUES (?, ?)
            """, (player_name, value))
            total_inserted += 1

        time.sleep(1)

    conn.commit()
    conn.close()
    print(f"Inserted {total_inserted} players into the database.")

if __name__ == "__main__":
    scrape_ktc_rankings()
