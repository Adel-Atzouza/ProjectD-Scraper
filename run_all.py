import subprocess
import time
import sys
import os

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

for project_folder, _ in SPIDERS:
    full_path = os.path.abspath(project_folder)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

total = len(SPIDERS)

for index, (project_folder, spider_name) in enumerate(SPIDERS, 1):
    percent = int((index - 1) / total * 100)
    print(f"\n🕷️ Running {spider_name} ({index}/{total}) [{percent}% done]...")

    start = time.time()

    subprocess.run(
        ["python", "-m", "scrapy", "crawl", spider_name], 
        cwd=project_folder,
        )

    duration = time.time() - start
    print(f"✅ Finished {spider_name} in {duration:.2f}s")