import os
import json
from datetime import datetime
from .game_utils import stage_check, rename_week_num, convert_preseason_date

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
                    continue  # Duplicate game, skip without incrementing change counter
                seen_games.add(game_tuple)

                # Set the stage field
                stage = stage_check(game, game.get("week_num", ""))
                if game.get("stage") != stage:
                    game["stage"] = stage
                    total_changes += 1

                # Correct `week_num` for specific playoff rounds
                new_week_num = rename_week_num(game.get("week_num", ""))
                if new_week_num != game["week_num"]:
                    game["week_num"] = new_week_num
                    total_changes += 1

                # Process game_date
                game_date = game.get("game_date", "")
                try:
                    # If already in YYYY-MM-DD format, skip correction
                    if len(game_date) == 10 and game_date[4] == '-' and game_date[7] == '-':
                        # Check if the date can be parsed as it is
                        datetime.strptime(game_date, "%Y-%m-%d")
                    else:
                        # Handle Pre Season games or dates in Month day format
                        if game.get("stage") == "Pre Season" or not game_date.startswith(year):
                            corrected_date = convert_preseason_date(game_date, year)
                            if corrected_date and game_date != corrected_date:
                                game["game_date"] = corrected_date
                                total_changes += 1
                except ValueError:
                    print(f"Error: Cannot parse date '{game_date}' with year {year}")
                    continue  # Skip adding to cleaned_games if the date is invalid

                cleaned_games.append(game)

            # Sort games by 'game_date'
            cleaned_games.sort(
                key=lambda x: datetime.strptime(x["game_date"], "%Y-%m-%d") if "game_date" in x and x["game_date"] else datetime.min
            )

            # Write the cleaned and sorted data back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_games, f, indent=4)

    if total_changes == 0:
        print("Data clean. No changes needed.")
    else:
        print(f"Total changes made: {total_changes}")

if __name__ == "__main__":
    scrub_pfc_data()
