# functions/game_utils.py

from datetime import datetime

def is_duplicate(existing_data, new_data):
    """Check if new_data already exists in existing_data list."""
    for existing in existing_data:
        if existing == new_data:
            return True
    return False

def correct_date_format(date_str, year):
    """Convert a date in 'Month Day' format to 'YYYY-MM-DD' format."""
    try:
        date_parsed = datetime.strptime(date_str, "%B %d")
        corrected_date = date_parsed.replace(year=int(year))
        return corrected_date.strftime("%Y-%m-%d")
    except ValueError:
        return None

def convert_preseason_date(date_str, year):
    """Convert a 'Month Day' format to 'YYYY-MM-DD' using the provided year."""
    try:
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
