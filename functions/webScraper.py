# functions/webScraper.py

import os
import json
import time
from bs4 import BeautifulSoup
from modules import setup_driver
from .game_utils import is_duplicate, correct_date_format

MIN_EXECUTION_TIME = 6.5  # Minimum execution time in seconds per year

def parse_regular_season_data(soup):
    data = []
    table = soup.find('table', {'id': 'games'})
    if not table:
        print("No regular season table found on the page.")
        return data

    rows = table.find_all('tr', {'data-row': True})
    for row in rows:
        week_num = row.find('th', {'data-stat': 'week_num'}).text.strip() if row.find('th', {'data-stat': 'week_num'}) else None
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
            "stage": "Regular Season",
            "week_num": week_num,
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

def parse_preseason_data(soup):
    data = []
    table = soup.find('table', {'id': 'preseason'})
    if not table:
        print("No preseason table found on the page.")
        return data

    rows = table.find_all('tr', {'data-row': True})
    for row in rows:
        week_num = row.find('th', {'data-stat': 'week_num'}).text.strip() if row.find('th', {'data-stat': 'week_num'}) else None
        game_day_of_week = row.find('td', {'data-stat': 'game_day_of_week'}).text.strip() if row.find('td', {'data-stat': 'game_day_of_week'}) else None
        game_date = row.find('td', {'data-stat': 'boxscore_word'}).text.strip() if row.find('td', {'data-stat': 'boxscore_word'}) else None
        visitor_team = row.find('td', {'data-stat': 'visitor_team'}).text.strip() if row.find('td', {'data-stat': 'visitor_team'}) else None
        points = row.find('td', {'data-stat': 'points'}).text.strip() if row.find('td', {'data-stat': 'points'}) else None
        game_location = row.find('td', {'data-stat': 'game_location'}).text.strip() if row.find('td', {'data-stat': 'game_location'}) else None
        home_team = row.find('td', {'data-stat': 'home_team'}).text.strip() if row.find('td', {'data-stat': 'home_team'}) else None
        points_opp = row.find('td', {'data-stat': 'points_opp'}).text.strip() if row.find('td', {'data-stat': 'points_opp'}) else None

        game_data = {
            "stage": "Pre Season",
            "week_num": week_num,
            "game_day_of_week": game_day_of_week,
            "game_date": game_date,
            "visitor_team": visitor_team,
            "points": points,
            "game_location": game_location,
            "home_team": home_team,
            "points_opp": points_opp,
        }
        data.append(game_data)
    return data

def download_pfc_data(years):
    driver = setup_driver()
    regular_season_base_url = "https://www.pro-football-reference.com/years/{}/games.htm"

    for year in years:
        start_time = time.time()
        all_data = []

        try:
            regular_season_url = regular_season_base_url.format(year)
            driver.get(regular_season_url)
            print(f"Bot navigated to {regular_season_url}")

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            regular_season_data = parse_regular_season_data(soup)

            # Load existing data or create new
            output_path = os.path.join("games_by_year_data", f"games_in_{year}.json")
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)

            # Add new data if not duplicate
            for game in regular_season_data:
                if not is_duplicate(all_data, game):
                    all_data.append(game)

            # Save updated data to JSON
            os.makedirs("games_by_year_data", exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=4)
            print(f"Regular season data for {year} downloaded and saved as JSON.")

        except Exception as e:
            print(f"An error occurred while downloading regular season data for {year}: {e}")

        # Ensure the loop takes at least MIN_EXECUTION_TIME
        elapsed_time = time.time() - start_time
        if elapsed_time < MIN_EXECUTION_TIME:
            time.sleep(MIN_EXECUTION_TIME - elapsed_time)

    driver.quit()

def download_preseason_data(years):
    driver = setup_driver()
    preseason_base_url = "https://www.pro-football-reference.com/years/{}/preseason.htm"

    for year in years:
        start_time = time.time()
        all_data = []

        try:
            preseason_url = preseason_base_url.format(year)
            driver.get(preseason_url)
            print(f"Bot navigated to {preseason_url}")

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            preseason_data = parse_preseason_data(soup)

            # Load existing data or create new
            output_path = os.path.join("games_by_year_data", f"games_in_{year}.json")
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)

            # Add new data if not duplicate
            for game in preseason_data:
                if not is_duplicate(all_data, game):
                    all_data.append(game)

            # Save updated data to JSON
            os.makedirs("games_by_year_data", exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=4)
            print(f"Preseason data for {year} downloaded and saved as JSON.")

        except Exception as e:
            print(f"An error occurred while downloading preseason data for {year}: {e}")

        # Ensure the loop takes at least MIN_EXECUTION_TIME
        elapsed_time = time.time() - start_time
        if elapsed_time < MIN_EXECUTION_TIME:
            time.sleep(MIN_EXECUTION_TIME - elapsed_time)

    driver.quit()
