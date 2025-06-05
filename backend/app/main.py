import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List
import os
import shutil
import json
from collections import defaultdict
from openai import OpenAI


#DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "master.db"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_league_master_db(league_id: str, rosters: list) -> str:
    #Create a league-specific copy of master.db and populate team_ids based on Sleeper rosters
    if len(league_id) < 5:
        raise ValueError("League ID must be at least 5 characters long")

    suffix = league_id[-5:]
    source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "master.db"))
    target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", f"master_league_{suffix}.db"))
    
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"master.db not found at {source_path}")

    # Copy the base master.db
    shutil.copyfile(source_path, target_path)

    # Open the new league-specific DB
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()

    # Set team_id for all players based on Sleeper roster data
    for team in rosters:
        team_id = team["roster_id"]
        player_ids = team.get("players", [])
        for pid in player_ids:
            cursor.execute(
                "UPDATE master SET team_id = ? WHERE player_id = ?",
                (team_id, pid)
            )

    conn.commit()
    conn.close()
    print(f"✅ Assigned team_ids and saved league-specific DB: {target_path}")
    return target_path

def add_picks_to_db(league_id: str, rosters: list):
    suffix = league_id[-5:]
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", f"master_league_{suffix}.db"))
    fc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "fantasycalc_rankings.db"))

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"League DB not found at {db_path}")
    if not os.path.exists(fc_path):
        raise FileNotFoundError(f"FantasyCalc DB not found at {fc_path}")

    pick_years = [2026, 2027, 2028]
    pick_rounds = [1, 2, 3]
    picks = []

    # Step 1: Initialize default picks
    for team in rosters:
        team_id = team["roster_id"]
        for season in pick_years:
            for rnd in pick_rounds:
                picks.append({
                    "team_id": team_id,  # will be updated if traded
                    "season": season,
                    "round": rnd,
                })

    # Step 2: Process traded picks from Sleeper
    traded_res = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/traded_picks")
    if traded_res.status_code == 200:
        traded = traded_res.json()
        for t in traded:
            if (
                t.get("season") in map(str, pick_years) and
                t.get("round") in pick_rounds and
                t.get("owner_id") and
                t.get("roster_id")
            ):
                season = int(t["season"])
                rnd = t["round"]
                old_roster_id = t["roster_id"]
                new_owner_id = t["owner_id"]

                # Update team_id if there's a matching pick
                for pick in picks:
                    if pick["season"] == season and pick["round"] == rnd and pick["team_id"] == old_roster_id:
                        pick["team_id"] = new_owner_id

    # Step 3: Add name field
    for pick in picks:
        pick["name"] = f"{pick['season']} Round {pick['round']}"

    # Step 4: Load pick values from FantasyCalc
    conn_fc = sqlite3.connect(fc_path)
    cursor_fc = conn_fc.cursor()

    pick_values = {}
    cursor_fc.execute("SELECT player_name, value FROM rankings WHERE player_name LIKE '%Round%'")
    for name, value in cursor_fc.fetchall():
        pick_values[name] = value
    conn_fc.close()

    # Step 5: Insert into DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for pick in picks:
        name = pick["name"]
        team_id = pick["team_id"]
        value = pick_values.get(name, 0)

        cursor.execute("""
            INSERT INTO master (player_id, team_id, name, team, position, age, years_exp, value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            None,
            team_id,
            name,
            None,
            "PICK",
            None,
            None,
            value
        ))

    conn.commit()
    conn.close()
    print(f"✅ Added picks to league DB: {db_path}")


def summarize_league_db(db_path: str) -> dict:
    """
    Extracts a full summary of the league from the master.db file.

    Returns a dictionary structured like:
    {
        team_id_1: [
            {name, team, position, age, years_exp, value},
            ...
        ],
        team_id_2: [ ... ],
        ...
    }
    Sorted by team_id for readability.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch player and pick data for each team
    cursor.execute("""
        SELECT team_id, name, team, position, age, years_exp, value
        FROM master
        WHERE team_id IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    # Organize and sort by team_id
    league_summary = defaultdict(list)
    for team_id, name, team, position, age, years_exp, value in rows:
        league_summary[team_id].append({
            "name": name,
            "team": team,
            "position": position,
            "age": age,
            "years_exp": years_exp,
            "value": value
        })

    # Convert to regular dict and sort by team_id
    sorted_summary = {team_id: league_summary[team_id] for team_id in sorted(league_summary.keys())}
    return sorted_summary

def summarize_team_values(db_path: str) -> dict:
    """
    Summarizes each team's total and positional value from the master.db file.

    Returns:
    {
        team_id: {
            "total_value": int,
            "position_values": {
                "QB": float,
                "RB": float,
                "WR": float,
                "TE": float,
                "PICK": float
            }
        },
        ...
    }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT team_id, position, value
        FROM master
        WHERE team_id IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    summary = defaultdict(lambda: {
        "total_value": 0,
        "position_values": {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "PICK": 0}
    })

    for team_id, position, value in rows:
        if position not in summary[team_id]["position_values"]:
            continue  # Skip unexpected positions
        summary[team_id]["position_values"][position] += value
        summary[team_id]["total_value"] += value

    return dict(sorted(summary.items()))

import openai
import json

def generate_trade_suggestion(
    strategy_text: str,
    full_league_data: dict,
    league_summary: dict,
    user_team_id: int,
    openai_api_key: str,
    model: str = "gpt-4o"
) -> list:
    """
    Uses OpenAI GPT API (v1.x) to generate 3 trade suggestions for a given team.
    Returns a list of 3 structured trade dictionaries.
    """
    client = OpenAI(api_key=openai_api_key)

    messages = [
        {
            "role": "system",
            "content": "You are a fantasy football trade strategist. You help generate realistic dynasty trades using team archetypes and player value balance."
        },
        {
            "role": "user",
            "content": f"Here is the dynasty strategy document (Sunday Scrolls):\n\n{strategy_text}"
        },
        {
            "role": "user",
            "content": f"Here is the full league data (player rosters and picks by team):\n\n{json.dumps(full_league_data)}"
        },
        {
            "role": "user",
            "content": f"Here is a summarized league value report by team:\n\n{json.dumps(league_summary)}"
        },
        {
            "role": "user",
            "content": (
                f"I am team_id {user_team_id}. Based on the Sunday Scrolls and the league data above, "
                "determine my team archetype and generate 3 realistic trades with 3 different teams. "
                "Each trade should help both sides and fall within reasonable value range (~1000 point difference max). "
                "Return ONLY a JSON array of 3 trade objects, each with the following structure:\n\n"
                "[\n"
                "  {\n"
                "    \"user_team_id\": <int>,\n"
                "    \"user_trade_assets\": [\"<Player/Pick 1>\", ...],\n"
                "    \"user_total_value\": <float>,\n"
                "    \"target_team_id\": <int>,\n"
                "    \"target_trade_assets\": [\"<Player/Pick 1>\", ...],\n"
                "    \"target_total_value\": <float>,\n"
                "    \"justification\": \"<Why the trade makes sense for both teams>\"\n"
                "  },\n"
                "  ... (2 more like this)\n"
                "]"
            )
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )

    reply = response.choices[0].message.content

    try:
        return json.loads(reply)
    except json.JSONDecodeError:
        raise ValueError(f"GPT response was not valid JSON:\n{reply}")


class LeagueRequest(BaseModel):
    league_id: str
class PlayerRequest(BaseModel):
    league_id: str
    player_ids: List[str]

class LeagueRankingsRequest(BaseModel):
    league_id: str
    team_id: int

class TradeRequest(BaseModel):
    league_id: str
    team_id: int


@app.post("/sleeper/league")
def get_league_teams(data: LeagueRequest):
    league_id = data.league_id
    print(f"Fetching league data for ID: {league_id}")

    try:
        # 1. Get league metadata
        league_res = requests.get(f"https://api.sleeper.app/v1/league/{league_id}")
        if league_res.status_code != 200:
            raise HTTPException(status_code=404, detail="League not found")

        league = league_res.json()

        # Validate league type
        settings = league.get("settings", {})
        is_dynasty = True
        is_superflex = settings.get("position_qb", 0) >= 2 or settings.get("position_sf", 1) > 0

        if not (is_dynasty and is_superflex):
            raise HTTPException(status_code=400, detail="This tool only supports dynasty superflex leagues.")

        # 2. Get rosters and users
        rosters_res = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters")
        users_res = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users")

        if rosters_res.status_code != 200 or users_res.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch league data.")

        rosters = rosters_res.json()
        users = users_res.json()

        # ✅ Build league-specific DB using the rosters
        build_league_master_db(league_id, rosters)
        add_picks_to_db(league_id, rosters)

        # 3. Build team metadata
        teams = []
        for r in rosters:
            owner = next((u for u in users if u["user_id"] == r["owner_id"]), None)

            display_name = owner.get("display_name", "Unknown") if owner else "Unknown"
            team_name = owner.get("metadata", {}).get("team_name") or display_name
            avatar = owner.get("avatar", None) if owner else None

            teams.append({
                "team_id": r["roster_id"],
                "owner_id": r["owner_id"],
                "team_name": team_name,
                "owner_display_name": display_name,
                "avatar": avatar,
                "roster": r,
            })

        return {
            "league_id": league_id,
            "league_name": league.get("name", ""),
            "season": league.get("season", ""),
            "teams": teams,
            "settings": settings
        }

    except Exception as e:
        print("Server error in /sleeper/league:", e)
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/players/info")
def get_team_assets(data: dict):
    league_id = data.get("league_id")
    team_id = data.get("team_id")

    if not league_id or len(league_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid league ID")
    if team_id is None:
        raise HTTPException(status_code=400, detail="Missing team_id")

    suffix = league_id[-5:]
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", f"master_league_{suffix}.db"))

    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="League-specific DB not found")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT player_id, name, position, team, value
        FROM master
        WHERE team_id = ?
    """
    cursor.execute(query, (team_id,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "player_id": row[0],  # can be None for picks
            "name": row[1],
            "position": row[2],
            "team": row[3],
            "value": row[4]
        })

    return {"players": sorted(result, key=lambda x: x["value"], reverse=True)}

@app.post("/league-rankings")
def get_league_rankings(req: LeagueRankingsRequest):
    league_id = req.league_id
    team_id = req.team_id
    suffix = league_id[-5:]
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", f"master_league_{suffix}.db"))

    if not os.path.exists(db_path):
        return {"error": "League DB not found."}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    positions = ["QB", "RB", "WR", "TE", "PICK"]
    rankings = {}

    for pos in positions:
        # Aggregate total value per team for this position
        cursor.execute("""
            SELECT team_id, SUM(value) as total
            FROM master
            WHERE position = ? and team_id IS NOT NULL
            GROUP BY team_id
            ORDER BY total DESC
        """, (pos,))
        results = cursor.fetchall()
        
        sorted_team_ids = [int(row[0]) for row in results]
        total_teams = len(sorted_team_ids)

        if team_id in sorted_team_ids:
            rank = sorted_team_ids.index(team_id) + 1  # rank is 1-indexed
        else:
            rank = None  # No players of this position on this team

        rankings[pos] = {
            "rank": rank,
            "total_teams": total_teams
        }

    conn.close()
    return rankings

@app.post("/generate-trade")
def generate_trade(req: TradeRequest):
    league_id = req.league_id
    team_id = req.team_id
    suffix = league_id[-5:]

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", f"master_league_{suffix}.db"))
    if not os.path.exists(db_path):
        return {"error": f"Database not found at {db_path}"}

    scrolls_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "sunday_scrolls.txt"))
    if not os.path.exists(scrolls_path):
        return {"error": "Sunday Scrolls strategy document not found."}

    # Load required inputs
    full_league_data = summarize_league_db(db_path)
    league_summary = summarize_team_values(db_path)

    # Load your strategy doc (as plain text)
    with open(scrolls_path, "r") as f:
        strategy_text = f.read()

    # Call the LLM
    try:
        trades = generate_trade_suggestion(
            strategy_text=strategy_text,
            full_league_data=full_league_data,
            league_summary=league_summary,
            user_team_id=team_id,
            openai_api_key="keyhere"
        )
        return trades
    except Exception as e:
        return {"error": str(e)}


