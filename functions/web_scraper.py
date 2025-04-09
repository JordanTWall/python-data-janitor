import os
import json
import time
import traceback
from contextlib import contextmanager
from bs4 import BeautifulSoup
from modules import setup_driver
from .game_utils import is_duplicate, correct_date_format, stage_check, rename_week_num

MIN_EXECUTION_TIME = 7  # Minimum execution time in seconds per year
MAX_RETRIES = 5  # Maximum number of retries
RETRY_DELAY = 10  # Initial delay between retries in seconds

@contextmanager
def get_driver():
    driver = setup_driver()
    try:
        yield driver
    finally:
        driver.quit()

def parse_regular_season_data(soup):
    data = []
    table = soup.find('table', {'id': 'games'})
    if not table:
        print("No regular season table found on the page.")
        return data

    rows = table.find_all('tr', {'data-row': True})
    for row in rows:
        week_num_elem = row.find('th', {'data-stat': 'week_num'})
        week_num = week_num_elem.text.strip() if week_num_elem else None
        if week_num is None:
            continue  # Skip header rows or invalid week_num rows

        game_day_of_week = row.find('td', {'data-stat': 'game_day_of_week'}).text.strip() if row.find('td', {'data-stat': 'game_day_of_week'}) else None
        game_date = row.find('td', {'data-stat': 'game_date'}).text.strip() if row.find('td', {'data-stat': 'game_date'}) else None
        gametime = row.find('td', {'data-stat': 'gametime'}).text.strip() if row.find('td', {'data-stat': 'gametime'}) else None
        winner = row.find('td', {'data-stat': 'winner'}).text.strip() if row.find('td', {'data-stat': 'winner'}) else None
        loser = row.find('td', {'data-stat': 'loser'}).text.strip() if row.find('td', {'data-stat': 'loser'}) else None
        pts_win = row.find('td', {'data-stat': 'pts_win'}).text.strip() if row.find('td', {'data-stat': 'pts_win'}) else None
        pts_lose = row.find('td', {'data-stat': 'pts_lose'}).text.strip() if row.find('td', {'data-stat': 'pts_lose'}) else None
        yards_win = row.find('td', {'data-stat': 'yards_win'}).text.strip() if row.find('td', {'data-stat': 'yards_win'}) else None
        yards_lose = row.find('td', {'data-stat': 'yards_lose'}).text.strip() if row.find('td', {'data-stat': 'yards_lose'}) else None

        game_data = {
            "stage": stage_check({}, week_num),
            "week_num": rename_week_num(week_num),
            "game_day_of_week": game_day_of_week,
            "game_date": game_date,
            "gametime": gametime,
            "winner": winner,
            "loser": loser,
            "pts_win": pts_win,
            "pts_lose": pts_lose,
            "yards_win": yards_win,
            "yards_lose": yards_lose
        }
        data.append(game_data)
    return data

def parse_preseason_data(soup, year):
    data = []
    table = soup.find('table', {'id': 'preseason'})
    if not table:
        print("No preseason table found on the page.")
        return data

    rows = table.find_all('tr', {'data-row': True})
    for row in rows:
        week_num_elem = row.find('th', {'data-stat': 'week_num'})
        week_num = week_num_elem.text.strip() if week_num_elem else ""

        if week_num == "":  # Handle Hall of Fame game for years 2017 and onwards
            week_num = "Hall of Fame Game"

        game_day_of_week = row.find('td', {'data-stat': 'game_day_of_week'}).text.strip() if row.find('td', {'data-stat': 'game_day_of_week'}) else None
        game_date = row.find('td', {'data-stat': 'boxscore_word'}).text.strip() if row.find('td', {'data-stat': 'boxscore_word'}) else None
        visitor_team = row.find('td', {'data-stat': 'visitor_team'}).text.strip() if row.find('td', {'data-stat': 'visitor_team'}) else None
        points = row.find('td', {'data-stat': 'points'}).text.strip() if row.find('td', {'data-stat': 'points'}) else None
        game_location = row.find('td', {'data-stat': 'game_location'}).text.strip() if row.find('td', {'data-stat': 'game_location'}) else None
        home_team = row.find('td', {'data-stat': 'home_team'}).text.strip() if row.find('td', {'data-stat': 'home_team'}) else None
        points_opp = row.find('td', {'data-stat': 'points_opp'}).text.strip() if row.find('td', {'data-stat': 'points_opp'}) else None

        if year in range(2010, 2016) and year not in [2011, 2016, 2020] and week_num == "1":
            week_num = "Hall of Fame Game"
        elif year in range(2010, 2016) and year not in [2011, 2016, 2020] and week_num.isdigit():
            week_num = str(int(week_num) - 1)

        game_data = {
            "stage": "Pre Season",
            "week_num": week_num,
            "game_day_of_week": game_day_of_week,
            "game_date": correct_date_format(game_date, year),
            "visitor_team": visitor_team,
            "points": points,
            "game_location": game_location,
            "home_team": home_team,
            "points_opp": points_opp,
        }
        data.append(game_data)
    return data

def download_data_for_year(year, season_type, base_url, parse_function, retries=0):
    with get_driver() as driver:
        start_time = time.time()
        all_data = []

        try:
            url = base_url.format(year)
            driver.get(url)
            print(f"Bot navigated to {url}")

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            if season_type == "regular season":
                season_data = parse_function(soup)
            else:
                season_data = parse_function(soup, year)

            # Load existing data or create new
            output_path = os.path.join("games_by_year_data", f"games_in_{year}.json")
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)

            # Add new data if not duplicate
            for game in season_data:
                if not is_duplicate(all_data, game):
                    all_data.append(game)

            # Save updated data to JSON
            os.makedirs("games_by_year_data", exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=4)
            print(f"{season_type.capitalize()} data for {year} downloaded and saved as JSON.")

        except Exception as e:
            print(f"An error occurred while downloading {season_type} data for {year}: {e}")
            print(traceback.format_exc())
            if retries < MAX_RETRIES:
                print(f"Retrying ({retries + 1}/{MAX_RETRIES}) in {RETRY_DELAY * (retries + 1)} seconds...")
                time.sleep(RETRY_DELAY * (retries + 1))
                download_data_for_year(year, season_type, base_url, parse_function, retries + 1)
            else:
                print(f"Failed to download {season_type} data for {year} after {MAX_RETRIES} retries.")
                raise e

        # Ensure the loop takes at least MIN_EXECUTION_TIME
        elapsed_time = time.time() - start_time
        if elapsed_time < MIN_EXECUTION_TIME:
            time.sleep(MIN_EXECUTION_TIME - elapsed_time)

def download_pfc_data(years):
    for year in years:
        try:
            download_data_for_year(year, "regular season", "https://www.pro-football-reference.com/years/{}/games.htm", parse_regular_season_data)
        except Exception as e:
            print(f"Skipping {year} due to repeated errors: {e}")

def download_preseason_data(years):
    for year in years:
        try:
            download_data_for_year(year, "preseason", "https://www.pro-football-reference.com/years/{}/preseason.htm", parse_preseason_data)
        except Exception as e:
            print(f"Skipping {year} due to repeated errors: {e}")
