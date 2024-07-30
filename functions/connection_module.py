import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_mongo_client():
    try:
        connection_string = os.getenv("MONGO_DB_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("No connection string found in environment variables.")
        
        client = MongoClient(connection_string)
        return client

    except Exception as e:
        raise Exception(f"The following error occurred: {e}")

def get_database_and_collection(client, db_name="nicholasCageDB", collection_name="nfl_games_by_year"):
    try:
        database = client[db_name]
        collection = database[collection_name]
        return database, collection

    except Exception as e:
        raise Exception(f"Error accessing database or collection: {e}")
