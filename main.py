# main.py
import os
import argparse
import subprocess
import time
from dotenv import load_dotenv
from modules import get_mongo_client, get_database

from functions.data_check import check_missing_data_by_year
from functions.web_scraper import download_pfc_data, download_preseason_data
from functions.assign_team_ids_and_update_json import assign_team_ids_and_update_json
from functions.update_stage_week_and_date import update_stage_week_and_date
from functions.mongo_bleach import mongo_bleach
from functions.fetch_game_ids import fetch_game_ids_and_update_json
from functions.normalize_week_fields import normalize_week_fields

load_dotenv()

parser = argparse.ArgumentParser(description="NFL Game Data CLI")
parser.add_argument("action", choices=[
    "check", "download", "download_preseason", "scrub", 
    "mongo_scrub", "full_mongo_scrub", "download_all", 
    "mongo_test", "fetch_ids", "normalize_weeks"
], help="The action to perform.")

parser.add_argument("--team", help="Team to target (or 'all')")
parser.add_argument("--years", help="Years to target (e.g. '2011,2013,2015-2017')")
parser.add_argument("--date", help="Specific date (YYYY-MM-DD)")

args = parser.parse_args()

def parse_years(years_arg):
    if years_arg == "all":
        return "all"
    years = set()
    for part in years_arg.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            years.update(range(start, end + 1))
        else:
            years.add(int(part))
    return sorted(years)

years = parse_years(args.years) if args.years else None

if args.action == "check":
    client = get_mongo_client()
    db = get_database(client)

    collections = db.list_collection_names() if args.team == "all" else [args.team]
    total_missing = 0

    for collection in collections:
        missing = check_missing_data_by_year(db, collection)
        for year, count in sorted(missing.items()):
            if years == "all" or year in years:
                print(f"{collection.replace('_', ' ')} {year}: {count} games missing")
                total_missing += count

    print(f"\nTotal missing games: {total_missing}")
    client.close()

elif args.action == "download":
    download_pfc_data(list(range(2010, 2024)) if years == "all" else years)

elif args.action == "download_preseason":
    download_preseason_data(list(range(2010, 2024)) if years == "all" else years)

elif args.action == "download_all":
    def run(command):
        retries = 0
        while retries < 5:
            try:
                if subprocess.run(command, shell=True, timeout=120, check=True).returncode == 0:
                    return True
            except subprocess.TimeoutExpired:
                print("Timeout. Retrying...")
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}. Retrying...")
            retries += 1
            time.sleep(10)
        return False

    for year in range(2010, 2024):
        print(f"Downloading year {year}...")
        run(f"python main.py download_preseason --years {year}")
        run(f"python main.py download --years {year}")

elif args.action == "fetch_ids":
    fetch_game_ids_and_update_json()
    
elif args.action == "normalize_weeks":
    
    print("🔧 Normalizing game.week values (adding 'Week ' prefix where needed)...")
    normalize_week_fields()

elif args.action == "full_mongo_scrub":
    print("✅ Assigning team IDs to JSON...")
    assign_team_ids_and_update_json()
    
    print("✅ Fetching game IDs from MongoDB...")
    fetch_game_ids_and_update_json()
    
    print("✅ Updating stage/week/date fields...")
    update_stage_week_and_date()
    
    print("✅ Final bleach pass...")
    mongo_bleach()
    
    print("🔧 Normalizing game.week values (adding 'Week ' prefix where needed)...")
    normalize_week_fields()


