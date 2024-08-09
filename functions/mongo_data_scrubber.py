import os
import json
from pymongo import MongoClient
from datetime import datetime
from modules import get_mongo_client, get_database
from functions.game_utils import find_game_by_date, update_game_stage_and_week

def mongo_data_scrubber(db, years=None, team=None):
    total_scrubbed = 0

    # Determine the teams to process
    if team == "all":
        collections = db.list_collection_names()
    else:
        collections = [team.replace(" ", "_")]

    for collection_name in collections:
        print(f"Processing team: {collection_name.replace('_', ' ')}")
        collection = db[collection_name]
        
        query = {
            "$and": [
                {"$or": [{"games.game.stage": None}, {"games.game.week": None}]}
            ]
        }
        if years:
            query["$and"].append({"parameters.season": {"$in": [str(year) for year in years]}})
        
        # Query all games that have missing stage or week
        documents = collection.find(query)

        scrubbed_count = 0

        for document in documents:
            season = document["parameters"]["season"]
            for game in document["games"]:
                if game["game"].get("stage") is None or game["game"].get("week") is None:
                    game_date = game["game"]["date"]["date"]
                    print(f"Scrubbing game on {game_date} for {collection_name.replace('_', ' ')}")

                    # Use the find_game_by_date function to locate the game
                    game_data, season = find_game_by_date(db, collection_name, game_date)
                    
                    if game_data:
                        # Update the game data in MongoDB if found
                        update_game_stage_and_week(db, collection_name, game, game_date, season)
                        scrubbed_count += 1

        total_scrubbed += scrubbed_count
        print(f"Data points scrubbed for {collection_name.replace('_', ' ')}: {scrubbed_count}")

    print(f"Total data points scrubbed: {total_scrubbed}")

if __name__ == "__main__":
    client = get_mongo_client()
    db = get_database(client)
    mongo_data_scrubber(db, years=[2010, 2011], team="all")
    client.close()
