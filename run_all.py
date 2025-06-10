import subprocess
import time
import sys
import os

# 🕷️ Lijst van alle spiders en bijbehorende projectmappen
SPIDERS = [
    ("GoudaScraper", "kwadraad_agenda"),
    ("GoudaScraper", "organisaties"),
    ("GoudaScraper", "goudabruist"),
    ("GoudaScraper", "sportpuntondersteuning_contacten_spider"),
    ("GoudaScraper", "sportaanbieders"),
    ("GoudaScraper", "zebra_zalen"),
    ("GoudaScraper", "sportcentrummammoet_zalen"),
    ("GoudaScraper", "gymzalen"),
    ("GoudaScraper", "groenhovenbad"),
    ("GoudaScraper", "dickvandijkhal_zalen"),
    ("GoudaScraper", "verhuur_buitensport"),
    ("GoudaScraper", "sportgouda_nieuws"),
    ("GoudaScraper", "sportpuntgouda_rooster"),
    ("GoudaScraper", "activities"),
    ("GoudaScraper", "algemene_info"),
    ("GoudaScraper", "contact_spider"),
    ("GoudaScraper", "sociaalteamgouda_spider"),
]

# Ensure project folders are in sys.path
for project_folder, _ in SPIDERS:
    full_path = os.path.abspath(project_folder)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)


def run_spider(project_folder, spider_name, index=None, total=None):
    label = f"({index}/{total})" if index and total else ""
    print(f"\n🕷️ Running {spider_name} {label}...")
    start = time.time()

    subprocess.run(
        ["python", "-m", "scrapy", "crawl", spider_name],
        cwd=project_folder,
    )

    duration = time.time() - start
    print(f"✅ Finished {spider_name} in {duration:.2f}s")


def show_menu():
    print("\n📋 Select an option:")
    print("0. Run all spiders")
    for idx, (_, spider_name) in enumerate(SPIDERS, 1):
        print(f"{idx}. Run spider: {spider_name}")
    print("q. Quit")


def main():
    while True:
        show_menu()
        choice = input("\nYour choice: ").strip().lower()

        if choice == "q":
            print("Exiting...")
            break
        elif choice == "0":
            total = len(SPIDERS)
            for index, (project, spider) in enumerate(SPIDERS, 1):
                run_spider(project, spider, index, total)
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(SPIDERS):
                project, spider = SPIDERS[idx - 1]
                run_spider(project, spider)
            else:
                print("⚠️ Invalid spider number.")
        else:
            print("⚠️ Invalid input. Try again.")


if __name__ == "__main__":
    main()
