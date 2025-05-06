import subprocess
import time
import sys
import os
from datetime import datetime

# 🕷️ Lijst van alle spiders en bijbehorende projectmappen
SPIDERS = [
    ("zoekenboekAgenda", "kwadraad_agenda"),
    ("goudawijzer", "organisaties"),
    ("goudawijzer", "goudabruist"),
    ("sportpunt", "sportpuntondersteuning_contacten_spider"),
    ("sportpunt", "sportaanbieders"),
    ("sportpunt", "zebra_zalen"),
    ("sportpunt", "sportcentrummammoet_zalen"),
    ("sportpunt", "gymzalen"),
    ("sportpunt", "groenhovenbad"),
    ("sportpunt", "dickvandijkhal_zalen"),
    ("sportpunt", "verhuur_buitensport"),
    ("sportpunt", "sportgouda_nieuws"),
    ("sportpunt", "sportpuntgouda_rooster"),
    ("sociaalteamgouda", "activities"),
    ("sociaalteamgouda", "algemene_info"),
    ("sociaalteamgouda", "contact_spider"),
    ("sociaalteamgouda", "sociaalteamgouda_spider"),
]

# 📁 Logbestand
LOG_FILE = "spider_run_log.txt"

# 🧾 Logging functie met tijdstempel
def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# 🕷️ Spider runner
def run_all_spiders():
    total = len(SPIDERS)
    log(f"🚀 Start scraping {total} spiders...")

    for index, (project_folder, spider_name) in enumerate(SPIDERS, 1):
        percent = int((index - 1) / total * 100)
        log(f"\n🕷️ ({index}/{total}) [{percent}%] Running spider: {spider_name}")

        full_path = os.path.abspath(project_folder)
        if full_path not in sys.path:
            sys.path.insert(0, full_path)

        start = time.time()

        try:
            subprocess.run(
                ["python", "-m", "scrapy", "crawl", spider_name],
                cwd=project_folder,
                check=True
            )
            duration = time.time() - start
            log(f"✅ Finished {spider_name} in {duration:.2f}s")

        except subprocess.CalledProcessError as e:
            log(f"❌ Error running spider '{spider_name}': {e}")

    log("🎉 All spiders completed.\n")

# ✅ Start de uitvoering direct
if __name__ == "__main__":
    run_all_spiders()
