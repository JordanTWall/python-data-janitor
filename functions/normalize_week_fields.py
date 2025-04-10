# scripts/normalize_week_labels.py
from modules.connection_module import get_mongo_client, get_database
from pymongo import UpdateOne

def normalize_week_fields():
    client = get_mongo_client()
    db = get_database(client)

    collections = db.list_collection_names()

    for collection_name in collections:
        collection = db[collection_name]
        print(f"🔍 Scanning collection: {collection_name}")

        bulk_updates = []

        for doc in collection.find({"games.game.week": {"$exists": True}}):
            updated = False
            for i, game in enumerate(doc.get("games", [])):
                week = game.get("game", {}).get("week")
                if week is None:
                    continue

                # Normalize if it's an int or string number (e.g. 3 or "3")
                if (isinstance(week, int) or (isinstance(week, str) and week.isdigit())):
                    doc["games"][i]["game"]["week"] = f"Week {week}"
                    updated = True

            if updated:
                bulk_updates.append(
                    UpdateOne({"_id": doc["_id"]}, {"$set": {"games": doc["games"]}})
                )

        if bulk_updates:
            result = collection.bulk_write(bulk_updates)
            print(f"✅ {collection_name}: {result.modified_count} week values normalized.")
        else:
            print(f"➖ {collection_name}: no changes needed.")

    client.close()
    print("🎉 Done normalizing week fields.")

if __name__ == "__main__":
    normalize_week_fields()
