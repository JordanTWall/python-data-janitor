import os
import json
from pymongo import MongoClient
from datetime import datetime
from .game_utils import stage_check, rename_week_num, convert_preseason_date

GAMES_FOLDER = "games_by_year_data"

def mongo_data_scrubber(db, years="all", teams="all"):
    total_changes = 0
    teams_data = json.load(open('data/teams.json'))["response"]
    team_map = {team["name"]: team["id"] for team in teams_data}

    # Determine which teams to process
    if teams == "all":
        team_names = list(team_map.keys())
    else:
        team_names = [team for team in teams if team in team_map]

    for team_name in team_names:
        print(f"Data scrubbing {team_name}")
        collection = db[f"nfl_games_by_year.{team_name.replace(' ', '_')}"]
        for year in (range(2010, 2023) if years == "all" else years):
            missing_games = collection.find({"$and": [{"game.stage": None}, {"game.week": None}]})
            games_to_update = []

            for doc in missing_games:
                game = doc.get("game", {})
                date_str = game.get("date", {}).get("date", "")
                home_team = doc.get("teams", {}).get("home", {}).get("name", "")
                away_team = doc.get("teams", {}).get("away", {}).get("name", "")
                season = int(doc.get("league", {}).get("season", ""))

                if not date_str or not home_team or not away_team or not season:
                    print(f"Skipping due to missing data: {doc}")
                    continue

                # Correct for Super Bowl in the following calendar year
                if season != int(date_str.split("-")[0]):
                    if season + 1 == int(date_str.split("-")[0]):
                        pass  # Continue as this is a Super Bowl game
                    else:
                        continue

                # Match game with local JSON data
                try:
                    with open(os.path.join(GAMES_FOLDER, f"games_in_{season}.json"), 'r', encoding='utf-8') as f:
                        games_data = json.load(f)
                    
                    for g in games_data:
                        if (g["game_date"] == date_str and 
                            g["home_team"] == home_team and 
                            g["visitor_team"] == away_team):
                            stage = g.get("stage")
                            week = g.get("week_num")
                            if stage and week:
                                games_to_update.append({"_id": doc["_id"], "stage": stage, "week": week})
                            break
                except FileNotFoundError:
                    print(f"Data file for season {season} not found.")
                except json.JSONDecodeError:
                    print(f"Error decoding JSON for season {season}.")

            # Update games in the database
            for game in games_to_update:
                collection.update_one(
                    {"_id": game["_id"]},
                    {"$set": {"game.stage": game["stage"], "game.week": game["week"]}}
                )
                total_changes += 1
            print(f"{year} season: {len(games_to_update)} games data scrubbed.")

    print(f"Total changes made: {total_changes}")
