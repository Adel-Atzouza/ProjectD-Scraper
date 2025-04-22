from selenium import webdriver
from bs4 import BeautifulSoup
import csv
import time

driver = webdriver.Chrome()
driver.get("https://www.sportpuntgouda.nl/rooster")
time.sleep(1)  # geef JS tijd om te laden

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Vind de juiste tabel
table = soup.select_one("table.planner-table")
rows = table.select("tr") if table else []

activiteiten = []
huidige_datum = None

for row in rows:
    # Datumregel herkennen
    datum_th = row.find("th", colspan="4")
    if datum_th:
        huidige_datum = datum_th.get_text(strip=True)
        continue

    cols = row.find_all("td")
    if len(cols) < 3:
        continue

    tijd = cols[0].get_text(strip=True)
    activiteit = cols[1].get_text(strip=True)
    faciliteit = cols[2].get_text(strip=True)

    activiteiten.append({
        "datum": huidige_datum,
        "tijd": tijd,
        "activiteit": activiteit,
        "faciliteit": faciliteit
    })

# Wegschrijven naar CSV
with open("sportpunt_rooster.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["datum", "tijd", "activiteit", "faciliteit"])
    writer.writeheader()
    writer.writerows(activiteiten)

print(f"✅ {len(activiteiten)} activiteiten opgeslagen in sportpunt_rooster.csv")
