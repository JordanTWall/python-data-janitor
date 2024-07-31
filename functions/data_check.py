# data_check.py
from pymongo import MongoClient

def check_missing_data_by_year(db, collection_name):
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
