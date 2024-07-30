import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB connection string from environment variables
MONGO_DB_CONNECTION_STRING = os.getenv("MONGO_DB_CONNECTION_STRING")

# Connect to MongoDB
client = MongoClient(MONGO_DB_CONNECTION_STRING)
db = client["nfl_games_by_year"]

# Initialize a total missing data counter
total_missing = 0

# Function to check missing data for a given team collection by year
def check_missing_data_by_year(collection_name):
    collection = db[collection_name]
    missing_data_by_year = {}

    for doc in collection.find({"$or": [{"games.game.stage": None}, {"games.game.week": None}]}):
        for game in doc.get("games", []):
            year = int(game["league"]["season"])
            if game["game"].get("stage") is None or game["game"].get("week") is None:
                if year not in missing_data_by_year:
                    missing_data_by_year[year] = 0
                missing_data_by_year[year] += 1

    return missing_data_by_year

# Iterate over each collection in the database
for collection_name in db.list_collection_names():
    missing_data = check_missing_data_by_year(collection_name)
    if missing_data:
        print(f"{collection_name.replace('_', ' ')} missing data:")
        for year, count in sorted(missing_data.items()):
            print(f"  {year}: missing data for {count} games")
        total_missing += sum(missing_data.values())

# Print the total number of missing data points
print(f"\nTotal missing data points: {total_missing}")
