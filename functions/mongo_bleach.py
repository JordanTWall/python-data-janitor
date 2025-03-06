import os
import json
from datetime import datetime
from modules.connection_module import get_mongo_client, get_database

def normalize_team_name(name):
    """Normalize team names to match MongoDB collection names."""
    name = name.title()
    name = name.replace("49Ers", "49ers")
    return name.replace(" ", "_")

def mongo_bleach():
    # Load team data from teams.json
    try:
        with open("data/teams.json", 'r', encoding='utf-8') as f:
            teams_data = json.load(f)
            print(f"Successfully loaded teams.json: {len(teams_data['response'])} teams found.")
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
    updated_games_count = 0
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Query MongoDB for all games with missing stage or week data
    print("Searching for games with missing stage or week data...")
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        cursor = collection.aggregate([
            {"$unwind": "$games"},
            {"$match": {"$or": [{"games.game.stage": None}, {"games.game.week": None}]}}
        ])
        
        for result in cursor:
            game_id = result["games"]["game"]["id"]
            season = result["games"]["league"]["season"]

            # Find the corresponding game in the JSON files
            json_file_path = os.path.join(games_dir, f"games_in_{season}.json")
            if not os.path.exists(json_file_path):
                print(f"JSON file for season {season} not found.")
                continue

            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    games_data = json.load(f)

                for game in games_data:
                    if game.get("game_id") == game_id:
                        winner_id = game.get("winner_id")
                        loser_id = game.get("loser_id")

                        if not winner_id or not loser_id:
                            print(f"Skipping game due to missing winner_id or loser_id on {game['game_date']}.")
                            continue

                        # Determine the collection name based on the winner's team ID
                        correct_collection_name = team_id_to_collection_name.get(winner_id)
                        if not correct_collection_name:
                            print(f"Could not find collection name for winner_id: {winner_id}")
                            continue

                        
                        # Update the game data in MongoDB
                        update_result = collection.update_one(
                            {"_id": result["_id"], "games.game.id": game_id},
                            {"$set": {
                                "games.$.game.stage": game.get("stage"),
                                "games.$.game.week": game.get("week_num"),
                                "games.$.game.date.date": game.get("game_date"),
                                "games.$.teams.home.name": game["winner"] if winner_id == game["winner_id"] else game["loser"],
                                "games.$.teams.away.name": game["loser"] if winner_id == game["winner_id"] else game["winner"],
                                "games.$.teams.home.logo": team_id_to_logo.get(winner_id) if winner_id == game["winner_id"] else team_id_to_logo.get(loser_id),
                                "games.$.teams.away.logo": team_id_to_logo.get(loser_id) if winner_id == game["winner_id"] else team_id_to_logo.get(winner_id),
                            }}
                        )

                        if update_result.modified_count > 0:
                            print(f"Updated Game ID {game_id} in collection {collection_name}.")
                            updated_games_count += 1
                        break

            except FileNotFoundError:
                print(f"Error: File {json_file_path} not found.")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in file {json_file_path}: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")

    # Log any errors to a JSON file in the test_responses directory
    if error_log:
        os.makedirs("test_responses", exist_ok=True)
        error_log_path = os.path.join("test_responses", f"id_errors_{timestamp}.json")
        with open(error_log_path, 'w', encoding='utf-8') as error_file:
            json.dump(error_log, error_file, indent=4)
        print(f"Logged errors to {error_log_path}")

    print(f"Total games updated in MongoDB: {updated_games_count}")

    # Close the MongoDB client after processing all files
    client.close()

# Example usage
if __name__ == "__main__":
    mongo_bleach()
