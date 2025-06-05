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
MAX_CONCURRENT = 5
EXCLUDE_EXTENSIONS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar"]

def is_excluded(url: str) -> bool:
    return any(url.lower().endswith(ext) for ext in EXCLUDE_EXTENSIONS)

def clean_markdown_from_soup(soup):
    lines = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li", "ul", "ol", "a"]):
        text = el.get_text(strip=True)
        if text and len(text) > 20 and not re.search(r"cookie|toestemming", text, re.I):
            lines.append(text)
    return "\n\n".join(lines)

async def collect_internal_urls(crawler, start_url: str, batch_size=5) -> Set[str]:
    to_visit = set([start_url])
    visited = set()
    discovered = set()
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, markdown_generator=DefaultMarkdownGenerator())
    session_id = f"discovery_{urlparse(start_url).netloc}"

    while to_visit:
        current_batch = list(to_visit)[:batch_size]
        to_visit.difference_update(current_batch)
        visited.update(current_batch)
        print(f"\n [Batch discovery] {len(discovered) + 1} URLs")
        tasks = [crawler.arun(url, crawl_config, session_id=session_id) for url in current_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for url, res in zip(current_batch, results):
            if isinstance(res, Exception):
                print(f" {url}: {res}")
                continue
            if res.success and res.html:
                soup = BeautifulSoup(res.html, "html.parser")
                for tag in soup.find_all("a", href=True):
                    href = tag["href"]
                    full = urljoin(url, href)
                    parsed = urlparse(full)
                    if parsed.netloc == urlparse(start_url).netloc:
                        norm = parsed.scheme + "://" + parsed.netloc + parsed.path
                        if not is_excluded(norm) and norm not in visited and norm not in to_visit:
                            to_visit.add(norm)
                            discovered.add(norm)

    return discovered

async def crawl_parallel(urls: List[str], max_concurrent: int):
    print("\n=== Parallel Crawling gestart ===")
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join("output", date_str)
    os.makedirs(output_dir, exist_ok=True)

    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, markdown_generator=DefaultMarkdownGenerator())

    domain_results = defaultdict(list)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            tasks = [crawler.arun(url, crawl_config, session_id=f"batch_{i + j}") for j, url in enumerate(batch)]
            results_batch = await asyncio.gather(*tasks, return_exceptions=True)

            for url, res in zip(batch, results_batch):
                if isinstance(res, Exception):
                    print(f" Exception @ {url}: {res}")
                    continue
                elif res.success:
                    html = res.html
                    soup = BeautifulSoup(html, "html.parser")
                    titel = soup.title.string.strip() if soup.title else "Onbekend"
                    summary = clean_markdown_from_soup(soup)

                    result = {
                        "url": url,
                        "titel": titel,
                        "samenvatting": summary
                    }

                    netloc = urlparse(url).netloc
                    domain_results[netloc].append(result)
                    print(f" {url} (toegevoegd aan {netloc})")

    for domain, results in domain_results.items():
        filepath = os.path.join(output_dir, f"{domain}.json")
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
