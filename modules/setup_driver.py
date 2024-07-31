# modules/setup_driver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

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
