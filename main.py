# main.py

import os
import argparse
from dotenv import load_dotenv
from tqdm import tqdm
from modules import get_mongo_client, get_database
from functions.data_check import check_missing_data_by_year
from functions.webScraper import download_pfc_data, download_preseason_data
from functions.pfc_data_scrubber import scrub_pfc_data
from functions.mongo_data_scrubber import mongo_data_scrubber  # Import the new function

# Load environment variables from .env file
load_dotenv()

# Initialize the argument parser
parser = argparse.ArgumentParser(description="Check for missing data in the NFL games database or download game data.")
parser.add_argument("action", choices=["check", "download", "download_preseason", "scrub", "mongo_scrub"], help="The action to perform.")
parser.add_argument("--team", help="The specific team to check. Use 'all' to check all teams.")
parser.add_argument("--years", help="Comma-separated list of specific years or year ranges to check or download (e.g., '2011,2013,2011-2013'). Use 'all' to check/download all years.")

args = parser.parse_args()

# Helper function to parse years argument
def parse_years(years_arg):
    if years_arg == "all":
        return "all"
    years = set()
    try:
        for part in years_arg.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                years.update(range(start, end + 1))
            else:
                years.add(int(part))
        return sorted(years)
    except ValueError:
        raise argparse.ArgumentTypeError("Years must be a comma-separated list of integers or ranges in 'YYYY-YYYY' format.")

# Parse the years argument
years = parse_years(args.years)

if args.action == "check":
    # Connect to MongoDB
    client = get_mongo_client()
    db = get_database(client)

    total_missing = 0
    if args.team == "all":
        collections = db.list_collection_names()
    else:
        collections = [args.team]

    for collection_name in collections:
        missing_data = check_missing_data_by_year(db, collection_name)
        if missing_data:
            print(f"\n{collection_name.replace('_', ' ')} missing data:")
            for year, count in sorted(missing_data.items()):
                if years == "all" or year in years:
                    print(f"  {year}: missing data for {count} games")
                    total_missing += count

    # Print the total number of missing data points
    print(f"\nTotal missing data points: {total_missing}")

    # Close the MongoDB client
    client.close()

elif args.action == "download":
    if years == "all":
        years = list(range(2010, 2023))  
    download_pfc_data(years)

elif args.action == "download_preseason":
    if years == "all":
        years = list(range(2010, 2023))  
    download_preseason_data(years)

elif args.action == "scrub":
    total_files = len([name for name in os.listdir("games_by_year_data") if name.startswith("games_in_") and name.endswith(".json")])
    with tqdm(total=total_files, desc="Scrubbing data", unit="file") as pbar:
        scrub_pfc_data(progress_bar=pbar)

elif args.action == "mongo_scrub":
    # Connect to MongoDB
    client = get_mongo_client()
    db = get_database(client)

    if years == "all":
        years = list(range(2010, 2023))  # or set a specific range if known
    # Call the mongo_data_scrubber function with the proper arguments
    mongo_data_scrubber(db, years, args.team)
    client.close()
