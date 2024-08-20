import os
import json
from datetime import datetime
from modules.connection_module import get_mongo_client, get_database

def normalize_team_name(name):
    """Normalize team names to match MongoDB collection names."""
    name = name.title()
    name = name.replace("49Ers", "49ers")
    return name.replace(" ", "_")

def update_stage_week_and_date():
    try:
        with open("data/teams.json", 'r', encoding='utf-8') as f:
            teams_data = json.load(f)
            print(f"Successfully loaded teams.json: {len(teams_data['response'])} teams found.")

            # Create a mapping from team ID to properly formatted collection names
            team_id_to_collection_name = {team["id"]: normalize_team_name(team["name"]) for team in teams_data["response"]}
            team_id_to_logo = {team["id"]: team["logo"] for team in teams_data["response"]}

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
    scrubbed_games_count = 0
    updated_games_count = 0
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    for filename in os.listdir(games_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(games_dir, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    games_data = json.load(f)
                    print(f"Loaded {filename}: {len(games_data)} games found.")

                for game in games_data:
                    if "game_id" not in game:
                        print(f"Skipping game without game_id on {game['game_date']}.")
                        continue  # Skip to the next game if no game_id is found

                    game_id = game["game_id"]
                    winner_id = game.get("winner_id")
                    loser_id = game.get("loser_id")

                    if not winner_id or not loser_id:
                        print(f"Missing winner_id or loser_id for game on {game['game_date']}. Skipping.")
                        continue  # Skip to the next game if either winner_id or loser_id is missing

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
                                db_game["game"]["stage"] = game.get("stage", db_game["game"]["stage"])
                                db_game["game"]["week"] = game.get("week_num", db_game["game"]["week"])
                                db_game["game"]["date"]["date"] = game.get("game_date", db_game["game"]["date"]["date"])

                                # Update home and away teams and logos based on winner and loser IDs
                                for team_type, team_id in {"home": db_game["teams"]["home"]["id"], "away": db_game["teams"]["away"]["id"]}.items():
                                    if team_id == winner_id:
                                        correct_team_name = game["winner"]
                                        correct_team_logo = team_id_to_logo.get(winner_id)
                                    elif team_id == loser_id:
                                        correct_team_name = game["loser"]
                                        correct_team_logo = team_id_to_logo.get(loser_id)
                                    else:
                                        continue  # Skip if the team ID doesn't match

                                    # Special case for Washington Redskins logo
                                    if correct_team_name == "Washington Redskins":
                                        correct_team_logo = "https://content.sportslogos.net/logos/7/168/full/im5xz2q9bjbg44xep08bf5czq.png"

                                    # Update MongoDB with corrected values
                                    db_game["teams"][team_type]["name"] = correct_team_name
                                    db_game["teams"][team_type]["logo"] = correct_team_logo

                                # Save the updated game back to MongoDB
                                collection.update_one(
                                    {"games.game.id": game_id},
                                    {"$set": {"games.$": db_game}}
                                )
                                print(f"Updated Game ID {game_id} for The {correct_team_name}")

                                scrubbed_games_count += 1
                                updated_games_count += 1
                                break
                    else:
                        error_message = f"Game with ID {game_id} not found in collection {collection_name}."
                        print(error_message)
                        error_log.append({
                            "game_id": game_id,
                            "winner": game.get("winner"),
                            "loser": game.get("loser"),
                            "game_date": game.get("game_date"),
                            "season": game.get("season"),
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

    print(f"Total games updated in MongoDB: {updated_games_count}")

    # Close the MongoDB client after processing all files
    client.close()
