import os
import json
import time
from datetime import datetime
from bson import ObjectId
from modules import get_mongo_client, get_database
from functions.game_utils import find_game_by_date, update_game_stage_and_week

def mongo_test():
    client = get_mongo_client()
    db = get_database(client)
    
    team = "Pittsburgh Steelers"  # Hardcoded for now, change as needed
    game_date = "2011-02-06"  # Hardcoded for now, change as needed

    team_name = team.replace(" ", "_")

    # Find the game for the given date
    game, season = find_game_by_date(db, team_name, game_date)

    if not game:
        print(f"No game found for team {team} on date {game_date}")
        return

    print(f"Found {team} game data on {game_date}")

    # Update stage and week if they are null
    if season:
        update_game_stage_and_week(db, team_name, game, game_date, season)

    # Create the test_responses directory if it doesn't exist
    os.makedirs("test_responses", exist_ok=True)

    # Save the result to a JSON file with the timestamp as the filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = os.path.join("test_responses", f"{timestamp}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(game, f, indent=4)

    print(f"Game data saved to {file_path}")

if __name__ == "__main__":
    mongo_test()
