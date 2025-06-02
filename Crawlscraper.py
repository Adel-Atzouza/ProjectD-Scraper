import os
import asyncio
import psutil
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Set
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# -------------------- CONFIG --------------------
# Start-URL(s) voor de crawler.
START_URLS = [
    # "https://sociaalteamgouda.nl/sitemap_index.xml",
    #"https://in-gouda.nl/sitemap_index.xml",
    "https://www.sportpuntgouda.nl/"
    # "https://www.kwadraad.nl/sitemap_index.xml"
    # "https://www.goudawijzer.nl/"
]
# Maximaal aantal gelijktijdige requests
MAX_CONCURRENT = 5
# Bestands-extensies die uitgesloten moeten worden van crawling
EXCLUDE_EXTENSIONS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar"]

# -------------------- FILTER --------------------
def is_excluded(url: str) -> bool:
    """
    Controleert of een URL eindigt op een van de uitgesloten extensies.
    """
    return any(url.lower().endswith(ext) for ext in EXCLUDE_EXTENSIONS)

# -------------------- BATCHED URL DISCOVERY --------------------
async def collect_internal_urls(crawler, start_url: str, batch_size=5) -> Set[str]:
    """
    Verzamelt alle interne links vanaf een start-URL, in batches.
    - crawler: de AsyncWebCrawler instantie
    - start_url: de URL waar vanaf gestart wordt
    - batch_size: hoeveel URLs tegelijk worden opgehaald
    """
    to_visit = set([start_url])  # URLs die nog bezocht moeten worden
    visited = set()              # URLs die al bezocht zijn
    discovered = set()           # Alle gevonden interne URLs

    # Configuratie voor de crawler-run (geen cache, standaard markdown generator)
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator()
    )
    # Unieke sessie-ID voor deze run
    session_id = f"discovery_{urlparse(start_url).netloc}"

    # Zolang er nog te bezoeken URLs zijn
    while to_visit:
        # Pak een batch van te bezoeken URLs
        current_batch = list(to_visit)[:batch_size]
        to_visit.difference_update(current_batch)
        visited.update(current_batch)

        print(f"\n🔎 [Batch discovery] {len(discovered) + 1} URLs")
        # Start asynchroon crawlen van de batch
        tasks = [crawler.arun(url, crawl_config, session_id=session_id) for url in current_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verwerk de resultaten van de batch
        for url, res in zip(current_batch, results):
            if isinstance(res, Exception):
                print(f"❌ {url}: {res}")  # Fout bij ophalen
                continue
            if res.success and res.html:
                # HTML parsen en alle <a href=""> tags zoeken
                soup = BeautifulSoup(res.html, "html.parser")
                for tag in soup.find_all("a", href=True):
                    href = tag["href"]
                    full = urljoin(url, href)  # Maak absolute URL
                    parsed = urlparse(full)
                    # Alleen interne links (zelfde domein)
                    if parsed.netloc == urlparse(start_url).netloc:
                        # Normaliseer URL (zonder query/fragment)
                        norm = parsed.scheme + "://" + parsed.netloc + parsed.path
                        # Voeg toe als nog niet bezocht, niet uitgesloten, en nog niet in de queue
                        if not is_excluded(norm) and norm not in visited and norm not in to_visit:
                            to_visit.add(norm)
                            discovered.add(norm)

    return discovered  # Geef alle gevonden interne URLs terug

# -------------------- BATCHED SCRAPING --------------------
async def crawl_parallel(urls: List[str], max_concurrent: int):
    """
    Crawlt een lijst van URLs in parallelle batches.
    - urls: lijst van te crawlen URLs
    - max_concurrent: maximaal aantal gelijktijdige requests
    """
    print("\n=== Parallel Crawling gestart ===")
    peak_memory = 0
    process = psutil.Process(os.getpid())

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    def log_mem(stage):
        """
        Logt het huidige en piek-geheugengebruik.
        """
        nonlocal peak_memory
        mem = process.memory_info().rss
        peak_memory = max(peak_memory, mem)
        print(f"{stage} Memory: {mem // (1024*1024)} MB | Peak: {peak_memory // (1024*1024)} MB")

    # Browserconfiguratie voor headless crawling
    browser_config = BrowserConfig(
        headless=True,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]
    )
    # Crawler-runconfiguratie (geen cache, standaard markdown)
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator()
    )

    success, fail = 0, 0  # Tellers voor geslaagde/mislukte crawls

    # Start de asynchrone webcrawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Verdeel de URLs in batches van max_concurrent grootte
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            log_mem(f"Voor batch {i // max_concurrent + 1}")

            # Start asynchroon crawlen van de batch
            tasks = [crawler.arun(url, crawl_config, session_id=f"batch_{i + j}") for j, url in enumerate(batch)]
            results_batch = await asyncio.gather(*tasks, return_exceptions=True)
            log_mem(f"Na batch {i // max_concurrent + 1}")

            # Verwerk de resultaten van de batch
            for url, res in zip(batch, results_batch):
                if isinstance(res, Exception):
                    print(f"❌ Exception @ {url}: {res}")
                    fail += 1
                elif res.success:
                    md = res.markdown.raw_markdown.strip()
                    print(f"✅ {url} (len={len(md)})")
                    success += 1

                    # --- Markdown opslaan naar txt-bestand ---
                    # Maak een bestandsveilige naam op basis van de URL
                    parsed = urlparse(url)
                    import re
                    safe_path = re.sub(r'[^a-zA-Z0-9_-]', '_', parsed.path.strip('/')) or "root"
                    filename = f"{parsed.netloc}_{safe_path}.txt"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(md)
                else:
                    print(f"❌ Failed @ {url}: {res.error_message}")
                    fail += 1

    print(f"\n🔚 Samenvatting: ✅ {success} | ❌ {fail}")

# -------------------- MAIN --------------------
async def main():
    """
    Hoofdfunctie: verzamelt interne links en crawlt deze.
    """
    # Browserconfiguratie voor de crawler
    browser_config = BrowserConfig(
        headless=True,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]
    )

    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        all_urls = set()
        # Voor elke start-URL: verzamel interne links
        for start_url in START_URLS:
            print(f"\n🌐 Interne links verzamelen vanaf: {start_url}")
            found_urls = await collect_internal_urls(crawler, start_url, batch_size=MAX_CONCURRENT)
            print(f"🔗 {len(found_urls)} gevonden vanaf {start_url}")
            all_urls.update(found_urls)

        print(f"\n🌍 Totaal unieke interne URLs: {len(all_urls)}")
        # Crawl alle gevonden interne links in parallelle batches
        await crawl_parallel(list(all_urls), MAX_CONCURRENT)

    finally:
        # Sluit de crawler netjes af
        await crawler.close()

# Start het programma als script
if __name__ == "__main__":
    asyncio.run(main())