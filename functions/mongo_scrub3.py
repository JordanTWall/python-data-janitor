import os
import json
from datetime import datetime, timedelta
from modules.connection_module import get_mongo_client, get_database

def normalize_team_name(name):
    """Normalize team names to match MongoDB collection names."""
    name = name.title()  # Convert to title case
    name = name.replace("49Ers", "49ers")
    return name.replace(" ", "_")

def update_stage_week_and_date():
    try:
        with open("data/teams.json", 'r', encoding='utf-8') as f:
            teams_data = json.load(f)
            print(f"Successfully loaded teams.json: {len(teams_data['response'])} teams found.")

            # Create a mapping from team ID to properly formatted collection names
            team_id_to_collection_name = {team["id"]: normalize_team_name(team["name"]) for team in teams_data["response"]}
            print(f"Team ID to collection name mapping: {team_id_to_collection_name}")

    except FileNotFoundError:
        print("Error: teams.json file not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in teams.json: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    # Connect to MongoDB
    client = get_mongo_client()
    db = get_database(client)

    games_dir = "games_by_year_data"
    error_log = []
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    for filename in os.listdir(games_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(games_dir, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    games_data = json.load(f)
                    print(f"Loaded {filename}: {len(games_data)} games found.")

                for game in games_data:
                    # Skip the game if it doesn't have a game ID
                    if "game_id" not in game:
                        print(f"Skipping game without game_id on {game['game_date']}.")
                        continue

                    winner_id = game.get("winner_id")
                    loser_id = game.get("loser_id")
                    game_date = game.get("game_date")
                    stage = game.get("stage")
                    week_num = game.get("week_num")
                    season = game.get("season")
                    game_id = game.get("game_id")

                    if not (winner_id and loser_id and game_date and stage and week_num and season):
                        print(f"Skipping game due to missing essential data: {game}")
                        continue

                    # Determine the collection name from the winner's team ID
                    collection_name = team_id_to_collection_name.get(winner_id)
                    if not collection_name:
                        print(f"Could not find collection name for winner_id: {winner_id}")
                        continue

                    collection = db[collection_name]

                    # Find the game in the MongoDB collection
                    document = collection.find_one({"games.game.id": game_id})
                    if document:
                        for db_game in document["games"]:
                            if db_game["game"]["id"] == game_id:
                                # Update stage, week, and date in MongoDB
                                db_game["game"]["stage"] = stage
                                db_game["game"]["week"] = week_num
                                db_game["game"]["date"]["date"] = game_date

                                # Update home and away teams and logos if they don't exist
                                if not game.get("home_team"):
                                    game["home_team"] = db_game["teams"]["home"]["name"]
                                    game["home_team_id"] = db_game["teams"]["home"]["id"]
                                    game["home_team_logo"] = db_game["teams"]["home"]["logo"]
                                
                                if not game.get("visitor_team"):
                                    game["visitor_team"] = db_game["teams"]["away"]["name"]
                                    game["visitor_team_id"] = db_game["teams"]["away"]["id"]
                                    game["visitor_team_logo"] = db_game["teams"]["away"]["logo"]

                                print(f"Updated game_id {game_id} with stage, week, date, and teams.")
                    else:
                        error_message = f"Game with ID {game_id} not found in collection {collection_name}."
                        print(error_message)
                        error_log.append({
                            "game_id": game_id,
                            "winner": game["winner"],
                            "loser": game["loser"],
                            "game_date": game_date,
                            "season": season,
                            "collection": collection_name,
                            "error": error_message
                        })

            except FileNotFoundError:
                print(f"Error: File {filename} not found.")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in file {filename}: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")

    # Log any errors to a JSON file in test_responses directory
    if error_log:
        os.makedirs("test_responses", exist_ok=True)
        error_log_path = os.path.join("test_responses", f"id_errors_{timestamp}.json")
        with open(error_log_path, 'w', encoding='utf-8') as error_file:
            json.dump(error_log, error_file, indent=4)
        print(f"Logged errors to {error_log_path}")

    # Close the MongoDB client after processing all files
    client.close()
