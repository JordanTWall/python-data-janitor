import os
import json
from datetime import datetime, timedelta
from modules.connection_module import get_mongo_client, get_database

def fetch_game_ids_and_update_json():
    # Load team names and IDs from teams.json
    try:
        with open("data/teams.json", 'r', encoding='utf-8') as f:
            teams_data = json.load(f)
            print(f"Successfully loaded teams.json: {len(teams_data['response'])} teams found.")
            team_name_to_id = {team["name"]: team["id"] for team in teams_data["response"]}
            print(f"Team to ID mapping created: {team_name_to_id}")
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
        if filename.startswith("games_in_") and filename.endswith(".json"):
            file_path = os.path.join(games_dir, filename)
            season = filename.split("_")[2].split(".")[0]  # Extract season from filename

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    games_data = json.load(f)
                    print(f"Loaded {filename}: {len(games_data)} games found.")

                for game in games_data:
                    # Skip the game if it already has a game ID
                    if "game_id" in game:
                        print(f"Skipping game on {game['game_date']} as it already has a game ID.")
                        continue

                    winner_id = game.get("winner_id")
                    loser_id = game.get("loser_id")
                    game_date = game.get("game_date")

                    if not (winner_id and loser_id and game_date):
                        print(f"Skipping game due to missing essential data: {game}")
                        continue

                    # Get the winner team's collection name
                    winner_team_name = next((team for team, team_id in team_name_to_id.items() if team_id == winner_id), None)
                    if not winner_team_name:
                        print(f"Could not find winner team name for winner_id: {winner_id}")
                        continue

                    # Normalize collection name (replace spaces with underscores)
                    collection_name = winner_team_name.replace(" ", "_")
                    collection = db[collection_name]

                    # Convert game_date to a datetime object
                    game_date_obj = datetime.strptime(game_date, "%Y-%m-%d")

                    # Check the game on the day before, the actual date, and the day after
                    found_game_id = False
                    for offset in [-1, 0, 1]:
                        check_date = (game_date_obj + timedelta(days=offset)).strftime("%Y-%m-%d")
                        document = collection.find_one({"parameters.season": str(season)})
                        if document:
                            matched_game = next((g for g in document["games"] if g["game"]["date"]["date"] == check_date), None)
                            if matched_game:
                                game_id = matched_game["game"]["id"]
                                game["game_id"] = game_id
                                print(f"Assigned game_id {game_id} for game on {check_date} (Original date: {game_date})")
                                found_game_id = True
                                break
                    else:
                        # If no match found by date, try to match by team IDs and score
                        for db_game in document.get("games", []):
                            db_winner_id = db_game["teams"]["home"]["id"] if db_game["scores"]["home"]["total"] > db_game["scores"]["away"]["total"] else db_game["teams"]["away"]["id"]
                            db_loser_id = db_game["teams"]["home"]["id"] if db_game["scores"]["home"]["total"] < db_game["scores"]["away"]["total"] else db_game["teams"]["away"]["id"]

                            if (db_winner_id == winner_id and db_loser_id == loser_id):
                                game_id = db_game["game"]["id"]
                                game["game_id"] = game_id
                                print(f"Assigned game_id {game_id} based on winner and loser ID match.")
                                found_game_id = True
                                break

                    if not found_game_id:
                        error_message = f"Unable to find ID for {game['winner']} vs {game['loser']} on {game_date}"
                        print(error_message)
                        error_log.append({
                            "winner": game["winner"],
                            "loser": game["loser"],
                            "game_date": game_date,
                            "season": season,
                            "error": error_message
                        })

                # Save the updated game data back to the JSON file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(games_data, f, indent=4)
                    print(f"Updated {filename} with game IDs.")

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
