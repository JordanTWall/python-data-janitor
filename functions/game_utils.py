from datetime import datetime, timedelta
import os
import json
from pymongo import MongoClient

# Utility functions for date manipulation and MongoDB updates

def is_duplicate(existing_data, new_data):
    """Check if new_data already exists in existing_data list."""
    for existing in existing_data:
        if existing == new_data:
            return True
    return False

def correct_date_format(date_str, year):
    """Convert a date in 'Month Day' format to 'YYYY-MM-DD' format."""
    try:
        if not isinstance(date_str, str):
            return None
        date_parsed = datetime.strptime(date_str, "%B %d")
        corrected_date = date_parsed.replace(year=int(year))
        return corrected_date.strftime("%Y-%m-%d")
    except ValueError:
        return None

def convert_preseason_date(date_str, year):
    """Convert a 'Month Day' format to 'YYYY-MM-DD' using the provided year."""
    try:
        if not isinstance(date_str, str):
            return None
        date_parsed = datetime.strptime(date_str, "%B %d")
        corrected_date = date_parsed.replace(year=int(year))
        return corrected_date.strftime("%Y-%m-%d")
    except ValueError:
        print(f"Error: Cannot parse date '{date_str}' with year {year}")
        return None

def stage_check(game, week_num):
    """Set the stage field based on the week_num."""
    if week_num == "WildCard":
        return "Post Season"
    elif week_num == "Division":
        return "Post Season"
    elif week_num == "ConfChamp":
        return "Post Season"
    elif week_num == "SuperBowl":
        return "Post Season"
    else:
        return "Regular Season"

def rename_week_num(week_num):
    """Rename week_num for specific playoff rounds."""
    if week_num == "Division":
        return "Divisional Round"
    elif week_num == "ConfChamp":
        return "Conference Championships"
    elif week_num == "SuperBowl":
        return "Super Bowl"
    return week_num

def update_game_date_in_mongodb(db, team_name, game_id, correct_date):
    """Update the game date in MongoDB with the correct date."""
    collection = db[team_name]
    result = collection.update_one(
        {"games.game.id": game_id},
        {"$set": {"games.$.game.date.date": correct_date}}
    )
    if result.modified_count > 0:
        print(f"Updated game ID {game_id} in MongoDB with the correct date: {correct_date}")
    else:
        print(f"Failed to update the game ID {game_id} in MongoDB.")

def find_game_by_date(db, team_name, game_date):
    """Find a game by date, also checking the day before and after."""
    year = int(game_date.split("-")[0])
    collection = db[team_name]

    # Attempt to find the game on the exact date
    document = collection.find_one({"parameters.season": str(year)})
    
    if document:
        print(f"Searching for game on the exact date: {game_date}")
        game = next((g for g in document["games"] if g["game"]["date"]["date"] == game_date), None)
        if game:
            return game, year

        # Try the day before
        previous_day = (datetime.strptime(game_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"Checking day -1: {previous_day}")
        game = next((g for g in document["games"] if g["game"]["date"]["date"] == previous_day), None)
        if game:
            update_game_date_in_mongodb(db, team_name, game["game"]["id"], previous_day)
            return game, year

        # Try the day after
        next_day = (datetime.strptime(game_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"Checking day +1: {next_day}")
        game = next((g for g in document["games"] if g["game"]["date"]["date"] == next_day), None)
        if game:
            update_game_date_in_mongodb(db, team_name, game["game"]["id"], next_day)
            return game, year

    # If not found, try the previous year (for post-season logic)
    document = collection.find_one({"parameters.season": str(year - 1)})
    
    if document:
        print(f"Searching for game in the previous year on the exact date: {game_date}")
        game = next((g for g in document["games"] if g["game"]["date"]["date"] == game_date), None)
        if game:
            return game, year - 1

        # Try the day before
        previous_day = (datetime.strptime(game_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"Checking day -1 in previous year: {previous_day}")
        game = next((g for g in document["games"] if g["game"]["date"]["date"] == previous_day), None)
        if game:
            update_game_date_in_mongodb(db, team_name, game["game"]["id"], previous_day)
            return game, year - 1

        # Try the day after
        next_day = (datetime.strptime(game_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"Checking day +1 in previous year: {next_day}")
        game = next((g for g in document["games"] if g["game"]["date"]["date"] == next_day), None)
        if game:
            update_game_date_in_mongodb(db, team_name, game["game"]["id"], next_day)
            return game, year - 1

    print(f"No game found for team {team_name} on date {game_date} in year {year} or {year - 1}")
    return None, None

def update_game_stage_and_week(db, team_name, game, game_date, season):
    """Update stage and week fields if they are null, and correct the date if necessary."""
    if game["game"]["stage"] is None and game["game"]["week"] is None:
        json_file_path = os.path.join("games_by_year_data", f"games_in_{season}.json")

        if not os.path.exists(json_file_path):
            json_file_path = os.path.join("games_by_year_data", f"games_in_{season - 1}.json")

        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                games_data = json.load(f)

            matching_game = next((g for g in games_data if g["game_date"] == game_date and (
                g.get("home_team") == game["teams"]["home"]["name"] or 
                g.get("visitor_team") == game["teams"]["away"]["name"]
            )), None)

            if matching_game:
                print(f"Found matching game in JSON file: {matching_game}")
                game["game"]["stage"] = matching_game["stage"]
                game["game"]["week"] = matching_game["week_num"]

                # If the date is off by a day, correct it in MongoDB
                if game["game"]["date"]["date"] != matching_game["game_date"]:
                    print(f"Updating correct date to MongoDB: {matching_game['game_date']}")
                    update_game_date_in_mongodb(db, team_name, game["game"]["id"], matching_game["game_date"])

                # Update the stage and week in MongoDB
                collection = db[team_name]
                result = collection.update_one(
                    {"games.game.id": game["game"]["id"]},
                    {"$set": {"games.$.game.stage": matching_game["stage"], "games.$.game.week": matching_game["week_num"]}}
                )
                print(f"Update result: {result.modified_count} documents modified.")
                if result.modified_count > 0:
                    print(f"Updated game in MongoDB with stage: {matching_game['stage']} and week: {matching_game['week_num']}")
                else:
                    print("Failed to update the game in MongoDB.")
        else:
            print(f"JSON file not found: {json_file_path}")
