import os
import json
from modules.connection_module import get_mongo_client, get_database
from functions.assign_team_ids_and_update_json import assign_team_ids_and_update_json
from functions.fetch_game_ids import fetch_game_ids_and_update_json
from functions.update_stage_week_and_date import update_stage_week_and_date
from functions.mongo_bleach import mongo_bleach

def run_full_mongo_scrub():
    print("\n🔄 Step 1: Assigning team IDs to JSON...")
    assign_team_ids_and_update_json()

    print("\n🔄 Step 2: Matching and inserting game IDs from MongoDB...")
    fetch_game_ids_and_update_json()

    print("\n🔄 Step 3: Updating stage, week, and corrected date fields...")
    update_stage_week_and_date()

    print("\n🔄 Step 4: Final bleach scrub to sync logos and names with DB...")
    mongo_bleach()

    print("\n✅ All scrubbing stages complete!")

if __name__ == "__main__":
    run_full_mongo_scrub()
