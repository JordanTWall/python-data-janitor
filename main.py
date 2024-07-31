# main.py

import os
import argparse
from dotenv import load_dotenv
from functions.webScraper import download_pfc_data
# main.py
from modules import get_mongo_client, get_database_and_collection, check_missing_data_by_year

# Your main script logic here

# Load environment variables from .env file
load_dotenv()

# Initialize the argument parser
parser = argparse.ArgumentParser(description="Check for missing data in the NFL games database or download game data.")
parser.add_argument("action", choices=["check", "download"], help="The action to perform.")
parser.add_argument("--team", help="The specific team to check, use 'all' to check all teams.")
parser.add_argument("--year", help="The specific year to check, use 'all' to check all years.")

args = parser.parse_args()

if args.action == "check":
    from functions.data_check import check_missing_data_by_year
    from modules import get_mongo_client, get_database_and_collection

    # Connect to MongoDB
    client = get_mongo_client()
    db, _ = get_database_and_collection(client)

    total_missing = 0
    if args.team == "all":
        collections = db.list_collection_names()
    else:
        collections = [args.team]

    for collection_name in collections:
        missing_data = check_missing_data_by_year(db, collection_name)
        if missing_data:
            if args.year == "all":
                print(f"{collection_name.replace('_', ' ')} missing data:")
                for year, count in sorted(missing_data.items()):
                    print(f"  {year}: missing data for {count} games")
                total_missing += sum(missing_data.values())
            elif int(args.year) in missing_data:
                print(f"{collection_name.replace('_', ' ')} missing data in {args.year}: {missing_data[int(args.year)]} games")
                total_missing += missing_data[int(args.year)]

    # Print the total number of missing data points
    print(f"\nTotal missing data points: {total_missing}")

    # Close the MongoDB client
    client.close()

elif args.action == "download":
    if args.year == "all":
        years = list(range(2016, 2023))  # Example range
    else:
        years = [int(args.year)]
    
    download_pfc_data(years)
