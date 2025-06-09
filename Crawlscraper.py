import os
import re
import json
import asyncio
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Set
from datetime import datetime
from collections import defaultdict
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

START_URLS = ["https://www.sportpuntgouda.nl/"]
MAX_CONCURRENT = 15  # aantal paralell request
EXCLUDE_EXTENSIONS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar"]

EXPORT_FORMAT = "json"  # >>> ADDED EXPORT OPTIONS >>> Change to 'csv' or 'txt' as needed


# filter voor urls
def is_excluded(url: str) -> bool:
    return any(url.lower().endswith(ext) for ext in EXCLUDE_EXTENSIONS)

# haal de relavante tekstblokken uit de html en haal cookies eruit


def clean_markdown_from_soup(soup):
    lines = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li", "ul", "ol", "a"]):
        text = el.get_text(strip=True)
        if text and len(text) > 50 and not re.search(r"cookie|toestemming", text, re.I):
            lines.append(text)
    return "\n\n".join(lines)

# site crawlen beginnend bij de start url en verzamelt zo alle links in
# batches van 5, maar kan ook 10 of 15. ligt aan het syteem waaropt tie
# runt


async def collect_internal_urls(crawler, start_url: str, batch_size=15) -> Set[str]:
    to_visit = set([start_url])
    visited = set()
    discovered = set()

    # crawl config.
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, markdown_generator=DefaultMarkdownGenerator())
    session_id = f"discovery_{urlparse(start_url).netloc}"  # unieke sessie-naam per domein

    # loop tot dat er geen urls meer te bezoeken zijn
    while to_visit:
        current_batch = list(to_visit)[:batch_size]  # Pakt een batch
        to_visit.difference_update(current_batch)  # haalt de batch uit de lijst
        visited.update(current_batch)

        print(f"\n [Batch discovery] {len(discovered) + 1} URLs")  # voortgang batch crawling
        # start crawl-taken voor de batch
        tasks = [crawler.arun(url, crawl_config, session_id=session_id) for url in current_batch]
        # voert alle taken tegelijk uit en vangt fouten op
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # verwerk resultaten van deze batch
        for url, res in zip(current_batch, results):  # loop door elk res gekoppeld aan url
            if isinstance(res, Exception):
                print(f" {url}: {res}")
                continue
            if res.success and res.html:
                soup = BeautifulSoup(res.html, "html.parser")
                # vind alle interne links op pagina
                for tag in soup.find_all("a", href=True):
                    href = tag["href"]
                    full = urljoin(url, href)  # maakt er een absulute url van. bijv /contact wordt https//..../contact
                    parsed = urlparse(full)

                    # chekc of url binnen het zelfde domein zit en voeg toe aan to_visit
                    if parsed.netloc == urlparse(start_url).netloc:
                        norm = parsed.scheme + "://" + parsed.netloc + parsed.path  # verwijdert onnodige dingen zoals query strings of anchors
                        if not is_excluded(norm) and norm not in visited and norm not in to_visit:
                            to_visit.add(norm)
                            discovered.add(norm)

    return discovered


async def crawl_parallel(urls: List[str], max_concurrent: int):
    print("\n=== Parallel Crawling gestart ===")

    # maak output map op datum
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join("output", date_str)
    os.makedirs(output_dir, exist_ok=True)

    # crawl config
    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, markdown_generator=DefaultMarkdownGenerator())

    domain_results = defaultdict(list)  # per domein verzamelen

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]  # Maak batch van de lijst urls(5/10)
            tasks = [
                crawler.arun(
                    url,
                    crawl_config,
                    session_id=f"batch_{i + j}") for j,
                url in enumerate(batch)]  # per url in de batch een taak
            results_batch = await asyncio.gather(*tasks, return_exceptions=True)  # runt tegelijk

            for url, res in zip(batch, results_batch):
                if isinstance(res, Exception):
                    print(f" Exception @ {url}: {res}")
                    continue
                elif res.success:
                    html = res.html
                    soup = BeautifulSoup(html, "html.parser")
                    # Titel ophalen van de pagina (valt terug op 'Onbekend')
                    titel = soup.title.string.strip() if soup.title else "Onbekend"
                    summary = clean_markdown_from_soup(soup)  # Maak samenvatting op basis van relevante tekst

                    result = {
                        "url": url,
                        "titel": titel,
                        "samenvatting": summary
                    }

                    netloc = urlparse(url).netloc  # het domein paken van de url, voor groepering
                    domain_results[netloc].append(result)  # toegevoegd aan dict
                    print(f" {url} (toegevoegd aan {netloc})")

    # Schrijf alles weg naar JSON-bestanden per domein
    for domain, results in domain_results.items():
        filepath_base = os.path.join(output_dir, domain)

        if EXPORT_FORMAT == "csv":
            filepath = filepath_base + ".csv"
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["url", "titel", "samenvatting"])
                writer.writeheader()
                writer.writerows(results)

        elif EXPORT_FORMAT == "txt":
            filepath = filepath_base + ".txt"
            with open(filepath, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(f"URL: {r['url']}\nTitel: {r['titel']}\nSamenvatting:\n{r['samenvatting']}\n\n{'-'*80}\n\n")

        else:  # default JSON
            filepath = filepath_base + ".json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSamenvatting opgeslagen per domein in map: {output_dir}")


async def main():
    browser_config = BrowserConfig(headless=True)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        all_urls = set()
        for start_url in START_URLS:
            print(f"\n Interne links verzamelen vanaf: {start_url}")
            found_urls = await collect_internal_urls(crawler, start_url, batch_size=MAX_CONCURRENT)
            print(f"🔗 {len(found_urls)} gevonden vanaf {start_url}")
            all_urls.update(found_urls)

        print(f"\n Totaal unieke interne URLs: {len(all_urls)}")
        await crawl_parallel(list(all_urls), MAX_CONCURRENT)

    finally:
        await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())
