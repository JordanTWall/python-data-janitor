import os
import json

def assign_team_ids_and_update_json():
    # Load the teams JSON file
    try:
        with open("data/teams.json", "r") as f:
            teams = json.load(f)
            print(f"Successfully loaded teams.json: {len(teams)} teams found.")  # Debug statement
    except FileNotFoundError:
        print("Error: teams.json file not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    # Create a mapping from team names to their IDs
    try:
        team_name_to_id = {team["name"]: team["id"] for team in teams}
        print(f"Team to ID mapping created: {team_name_to_id}")  # Debug statement
    except TypeError as e:
        print(f"Error processing teams data: {e}")
        return

    # Loop through all JSON files in the games_by_year_data directory
    games_dir = "games_by_year_data"
    for filename in os.listdir(games_dir):
        if filename.startswith("games_in_") and filename.endswith(".json"):
            file_path = os.path.join(games_dir, filename)
            season = filename.split("_")[2].split(".")[0]  # Extract season from filename

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    games_data = json.load(f)
                    print(f"Loaded {filename}: {len(games_data)} games found.")  # Debug statement

                for game in games_data:
                    home_team = game.get("home_team")
                    visitor_team = game.get("visitor_team")
                    game["season"] = season

                    if home_team in team_name_to_id:
                        game["home_team_id"] = team_name_to_id[home_team]
                    if visitor_team in team_name_to_id:
                        game["visitor_team_id"] = team_name_to_id[visitor_team]

                    # Determine the winner and loser for Pre Season games
                    if game["stage"] == "Pre Season":
                        home_points = int(game["points_opp"])
                        visitor_points = int(game["points"])
                        if home_points > visitor_points:
                            game["winner"] = home_team
                            game["winner_id"] = team_name_to_id.get(home_team)
                            game["loser"] = visitor_team
                            game["loser_id"] = team_name_to_id.get(visitor_team)
                        else:
                            game["winner"] = visitor_team
                            game["winner_id"] = team_name_to_id.get(visitor_team)
                            game["loser"] = home_team
                            game["loser_id"] = team_name_to_id.get(home_team)

                    # Handle Regular/Post Season games
                    if game.get("winner") in team_name_to_id:
                        game["winner_id"] = team_name_to_id[game["winner"]]
                    if game.get("loser") in team_name_to_id:
                        game["loser_id"] = team_name_to_id[game["loser"]]

                # Save the updated game data back to the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(games_data, f, indent=4)
                    print(f"Updated {filename} and saved changes.")  # Debug statement

            except FileNotFoundError:
                print(f"Error: {filename} not found.")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {filename}: {e}")

if __name__ == "__main__":
    assign_team_ids_and_update_json()
