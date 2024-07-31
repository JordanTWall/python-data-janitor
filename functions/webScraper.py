# functions/download_pfc.py

import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def setup_driver():
    chrome_options = Options()
    # Use the Chrome Headless Shell
    chrome_options.binary_location = "C:\\Users\\jorda\\OneDrive\\Desktop\\chrome\\chrome-headless-shell-win64\\chrome-headless-shell.exe"
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Specify the path to ChromeDriver
    service = Service("C:\\Users\\jorda\\OneDrive\\Desktop\\chrome\\chromedriver-win64\\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def parse_data_to_json(soup):
    data = []
    table = soup.find('table', {'id': 'games'})
    if not table:
        print("No table found on the page.")
        return data

    rows = table.find_all('tr', {'data-row': True})
    for row in rows:
        week_num = row.find('th', {'data-stat': 'week_num'})
        week_num = week_num.text.strip() if week_num else None

        game_day_of_week = row.find('td', {'data-stat': 'game_day_of_week'})
        game_day_of_week = game_day_of_week.text.strip() if game_day_of_week else None

        game_date = row.find('td', {'data-stat': 'game_date'})
        game_date = game_date.text.strip() if game_date else None

        gametime = row.find('td', {'data-stat': 'gametime'})
        gametime = gametime.text.strip() if gametime else None

        winner = row.find('td', {'data-stat': 'winner'})
        winner = winner.text.strip() if winner else None

        loser = row.find('td', {'data-stat': 'loser'})
        loser = loser.text.strip() if loser else None

        pts_win = row.find('td', {'data-stat': 'pts_win'})
        pts_win = pts_win.text.strip() if pts_win else None

        pts_lose = row.find('td', {'data-stat': 'pts_lose'})
        pts_lose = pts_lose.text.strip() if pts_lose else None

        yards_win = row.find('td', {'data-stat': 'yards_win'})
        yards_win = yards_win.text.strip() if yards_win else None

        yards_lose = row.find('td', {'data-stat': 'yards_lose'})
        yards_lose = yards_lose.text.strip() if yards_lose else None

        game_data = {
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

def download_pfc_data(years):
    driver = setup_driver()
    base_url = "https://www.pro-football-reference.com/years/{}/games.htm"

    for year in years:
        try:
            url = base_url.format(year)
            driver.get(url)
            print(f"Bot navigated to {url}")

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            data = parse_data_to_json(soup)

            # Save to JSON
            if data:
                output_path = os.path.join("games_by_year_data", f"games_in_{year}.json")
                os.makedirs("games_by_year_data", exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                print(f"Data for {year} downloaded and saved as JSON.")
            else:
                print(f"No data found for {year}.")
            
    

        except Exception as e:
            print(f"An error occurred while downloading data for {year}: {e}")

    driver.quit()
