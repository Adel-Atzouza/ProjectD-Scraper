import os
import sys

PROGRESS_FOLDER = "progress"

import re
import json
import asyncio
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm
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

MAX_CONCURRENT = 15
EXCLUDE_EXTENSIONS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar"]

def is_excluded(url: str) -> bool:
    return any(url.lower().endswith(ext) for ext in EXCLUDE_EXTENSIONS)

def clean_markdown_from_soup(soup):
    lines = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li", "ul", "ol", "a"]):
        text = el.get_text(strip=True)
        if text and len(text) > 50 and not re.search(r"cookie|toestemming", text, re.I):
            lines.append(text)
    return "\n\n".join(lines)

async def collect_internal_urls(crawler, start_url: str, batch_size=15) -> Set[str]:
    to_visit = set([start_url])
    visited = set()
    discovered = set()

    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, markdown_generator=DefaultMarkdownGenerator())
    session_id = f"discovery_{urlparse(start_url).netloc}"

    while to_visit:
        current_batch = list(to_visit)[:batch_size]
        to_visit.difference_update(current_batch)
        visited.update(current_batch)

        print(f"\n [Batch] {len(discovered) + 1} URLs...")
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

async def crawl_parallel(urls, max_concurrent, progress_file):
    print("\n=== Start parallel crawl ===")
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join("output", date_str)
    os.makedirs(output_dir, exist_ok=True)

    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, markdown_generator=DefaultMarkdownGenerator())
    domain_results = defaultdict(list)

    done_count = 0
    total_urls = len(urls)


    with open(progress_file, "w") as f:
        json.dump({"progress": 0, "status": "running"}, f)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            tasks = [crawler.arun(url, crawl_config, session_id=f"batch_{i + j}") for j, url in enumerate(batch)]
            results_batch = await asyncio.gather(*tasks, return_exceptions=True)

            for url, res in zip(batch, results_batch):
                done_count += 1
                percent_done = int((done_count / total_urls) * 100)

                with open(progress_file, "w") as f:
                    json.dump({"progress": percent_done, "status": "running" if percent_done < 100 else "done"}, f)
                    f.flush()
                    os.fsync(f.fileno())

                if isinstance(res, Exception):
                    print(f"{url}: {res}")
                    continue
                elif res.success:
                    soup = BeautifulSoup(res.html, "html.parser")
                    titel = soup.title.string.strip() if soup.title else "Onbekend"
                    summary = clean_markdown_from_soup(soup)
                    result = {"url": url, "titel": titel, "samenvatting": summary}
                    netloc = urlparse(url).netloc
                    domain_results[netloc].append(result)
                    print(f"{url} ({percent_done}%) saved to {netloc}")


    with open(progress_file, "w") as f:
        json.dump({"progress": 100, "status": "done"}, f)

    print(f"\n🎉 Done. Data saved in: {output_dir}")

async def run_one_url(url: str, job_id: str):
    progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")

    browser_config = BrowserConfig(headless=True)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    try:
        print(f"\n🌐 Crawling site: {url}")
        found_urls = await collect_internal_urls(crawler, url, batch_size=MAX_CONCURRENT)
        print(f"🔗 {len(found_urls)} links found for {url}")
        await crawl_parallel(list(found_urls), MAX_CONCURRENT, progress_file)
    finally:
        await crawler.close()


def update_progress(job_id, percent, status="running"):
    progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
    with open(progress_file, "w") as f:
        json.dump({"progress": percent, "status": status}, f)

# CLI entrypoint
if __name__ == "__main__":
    if len(sys.argv) > 2:
        url = sys.argv[1]
        job_id = sys.argv[2]
        try:
            asyncio.run(run_one_url(url, job_id))
        except Exception as e:
            update_progress(job_id, 100, f"error: {str(e)}")
    else:
        print("❌ Please provide URL and job_id")
