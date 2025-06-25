# fetcher.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Toggle this flag to switch modes
MAX_WEEKS_MODE = True
MAX_WEEKS = 52  # Only used if MAX_WEEKS_MODE is True


def get_event_links():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://zoekenboekgouda.kwadraad.nl/agenda")

    wait = WebDriverWait(driver, 6)
    links = set()
    week_count = 0

    while True:
        try:
            wait.until(EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "js-popup")))
            event_elements = driver.find_elements(By.CLASS_NAME, "js-popup")

            for elem in event_elements:
                link = elem.get_attribute("href")
                if link:
                    links.add(link)

            if MAX_WEEKS_MODE and week_count >= MAX_WEEKS:
                print(f"[INFO] Reached max weeks: {MAX_WEEKS}")
                break

            next_week_btn = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".calendar-form__date-next.js-date-next")
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", next_week_btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", next_week_btn)
            time.sleep(2)
            week_count += 1

        except Exception as e:
            print(f"[INFO] No more weeks or failed to click 'next week': {e}")
            break

    driver.quit()
    return list(links)


EVENT_LINKS = get_event_links()

# Optional: print the results
print(f"Total event links found: {len(EVENT_LINKS)}")
for link in EVENT_LINKS:
    print(link)
