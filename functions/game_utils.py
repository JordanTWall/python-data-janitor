from datetime import datetime
import os
import json

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

def find_game_by_date(db, team_name, game_date):
    year = int(game_date.split("-")[0])
    collection = db[team_name]

    # Find the document for the given year
    document = collection.find_one({"parameters.season": str(year)})
    print(f"Looking for year {year} in team {team_name} collection")

    if document:
        # Find the game for the given date
        game = next((g for g in document["games"] if g["game"]["date"]["date"] == game_date), None)
        if game:
            print(f"Game found for date {game_date} in year {year}")
            return game, year

    # If not found, try the previous year
    document = collection.find_one({"parameters.season": str(year - 1)})
    print(f"Looking for year {year - 1} in team {team_name} collection")

    if document:
        game = next((g for g in document["games"] if g["game"]["date"]["date"] == game_date), None)
        if game:
            print(f"Game found for date {game_date} in year {year - 1}")
            return game, year - 1

    print(f"No game found for team {team_name} on date {game_date} in year {year} or {year - 1}")
    return None, None

def update_game_stage_and_week(db, team_name, game, game_date, season):
    if game["game"]["stage"] is None and game["game"]["week"] is None:
        json_file_path = os.path.join("games_by_year_data", f"games_in_{season}.json")

        print(f"Initial JSON file path: {json_file_path}")

        if not os.path.exists(json_file_path):
            json_file_path = os.path.join("games_by_year_data", f"games_in_{season - 1}.json")
            print(f"Updated JSON file path to previous year: {json_file_path}")

        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                games_data = json.load(f)
            print(f"Loaded JSON file: {json_file_path}")

            matching_game = next((g for g in games_data if g["game_date"] == game_date and (
                g.get("home_team") == team_name.replace("_", " ") or 
                g.get("visitor_team") == team_name.replace("_", " ") or
                g.get("winner") == team_name.replace("_", " ") or
                g.get("loser") == team_name.replace("_", " ")
            )), None)

            if matching_game:
                print(f"Found matching game in JSON file: {matching_game}")
                game["game"]["stage"] = matching_game["stage"]
                game["game"]["week"] = matching_game["week_num"]

                # Update the game object in MongoDB
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
