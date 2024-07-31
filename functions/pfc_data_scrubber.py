# functions/pfc_data_scrubber.py

import os
import json
from datetime import datetime

GAMES_FOLDER = "games_by_year_data"

def scrub_pfc_data():
    total_changes = 0  # Initialize change counter
    for filename in os.listdir(GAMES_FOLDER):
        if filename.startswith("games_in_") and filename.endswith(".json"):
            year = filename.split("_")[2].split(".")[0]
            file_path = os.path.join(GAMES_FOLDER, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                games = json.load(f)

            cleaned_games = []
            seen_games = set()
            for game in games:
                # Remove duplicates
                game_tuple = tuple(sorted(game.items()))
                if game_tuple in seen_games:
                    total_changes += 1
                    continue
                seen_games.add(game_tuple)

                # Remove games with "week_num": "Week"
                if game.get("week_num") == "Week":
                    total_changes += 1
                    continue
                
                # Handle "week_num" empty or specific cases
                if not game.get("week_num") or game.get("week_num").strip() == "":
                    if not game.get("visitor_team") or not game.get("home_team"):
                        total_changes += 1
                        continue
                    else:
                        game["week_num"] = "Hall of Fame Game"
                        total_changes += 1

                # Ensure "stage" field is present
                if "stage" not in game:
                    week_num = game.get("week_num", "")
                    if week_num == "WildCard":
                        game["stage"] = "Post Season"
                    elif week_num == "Division":
                        game["stage"] = "Post Season"
                    elif week_num == "ConfChamp":
                        game["stage"] = "Post Season"
                    elif week_num == "SuperBowl":
                        game["stage"] = "Post Season"
                    elif week_num.isdigit() and int(week_num) <= 4:
                        game["stage"] = "Pre Season"
                    else:
                        game["stage"] = "Regular Season"
                    total_changes += 1
                elif game["stage"] == "Preseason":
                    game["stage"] = "Pre Season"
                    total_changes += 1

                # Correct `week_num` for specific playoff rounds
                if game.get("week_num") == "Division":
                    game["week_num"] = "Divisional Round"
                    total_changes += 1
                elif game.get("week_num") == "ConfChamp":
                    game["week_num"] = "Conference Championships"
                    total_changes += 1
                elif game.get("week_num") == "SuperBowl":
                    game["week_num"] = "Super Bowl"
                    total_changes += 1

                # Correct date format for Pre Season games
                if game.get("stage") == "Pre Season":
                    game_date = game.get("game_date", "")
                    if game_date:
                        try:
                            game_date_parsed = datetime.strptime(game_date, "%B %d")
                            corrected_date = game_date_parsed.replace(year=int(year))
                            if game["game_date"] != corrected_date.strftime("%Y-%m-%d"):
                                game["game_date"] = corrected_date.strftime("%Y-%m-%d")
                                total_changes += 1
                        except ValueError:
                            continue

                cleaned_games.append(game)

            # Sort games by 'game_date'
            cleaned_games.sort(key=lambda x: datetime.strptime(x["game_date"], "%Y-%m-%d") if "game_date" in x and x["game_date"] else datetime.min)

            # Write the cleaned and sorted data back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_games, f, indent=4)

    if total_changes == 0:
        print("Data clean. No changes needed.")
    else:
        print(f"Total changes made: {total_changes}")

if __name__ == "__main__":
    scrub_pfc_data()
