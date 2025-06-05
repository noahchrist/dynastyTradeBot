import requests
import sqlite3

# Define the API endpoint
url = "https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=2&numTeams=12&ppr=0.5"

# Fetch the data from the API
response = requests.get(url)
data = response.json()

# Connect to your SQLite database
conn = sqlite3.connect("./data/fantasycalc_rankings.db")
cursor = conn.cursor()

# Truncate the 'rankings' table before inserting new data
cursor.execute("DELETE FROM rankings")

# Insert data into the 'rankings' table and count rows
row_count = 0
for player in data:
    player_name = player['player']['name']
    value = player['value']
    cursor.execute("INSERT INTO rankings (player_name, value) VALUES (?, ?)", (player_name, value))
    row_count += 1

# Commit changes and close the connection
conn.commit()
conn.close()

print(f"added {row_count} rows to the rankings table")
