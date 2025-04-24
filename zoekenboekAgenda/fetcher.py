# fetcher.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import urllib.parse

def get_event_links():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://zoekenboekgouda.kwadraad.nl/agenda")

    wait = WebDriverWait(driver, 10)
    links = set()
    max_weeks = 5  # adjust depending on how far back/future you want to go

    for _ in range(max_weeks):
        time.sleep(2)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "js-popup")))
        event_elements = driver.find_elements(By.CLASS_NAME, "js-popup")

        for elem in event_elements:
            link = elem.get_attribute("href")
            if link:
                links.add(link)

        try:
            next_week_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".calendar-form__date-next.js-date-next"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", next_week_btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", next_week_btn)
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! !!!!!!!!!!!!!!!!!! !!!!!!!!!!!!!!! Could not click next week: {e}")

    driver.quit()
    return list(links)

EVENT_LINKS = get_event_links()
