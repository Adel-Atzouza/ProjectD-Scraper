import os
import sys
import re
import json
import asyncio
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from utils import is_excluded, clean_text, log_progress
import hashlib


PROGRESS_FOLDER = "progress"
MAX_CONCURRENT = 15


async def collect_internal_urls(
    crawler, start_url: str, batch_size: int, progress_file: str
):
    to_visit = set([start_url])
    visited = set()
    discovered = set()
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, markdown_generator=DefaultMarkdownGenerator()
    )
    session_id = f"discovery_{urlparse(start_url).netloc}"

    while to_visit:
        batch = list(to_visit)[:batch_size]
        to_visit.difference_update(batch)
        visited.update(batch)

        total = len(to_visit) + len(visited)
        progress = int((len(visited) / total) * 80) if total else 0
        log_progress(
            progress_file, progress, status="discovering", url=start_url
        )  # URL consistent doorgeven

        tasks = [
            crawler.arun(url, crawl_config, session_id=session_id) for url in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for url, res in zip(batch, results):
            if isinstance(res, Exception):
                continue
            if res.success and res.html:
                soup = BeautifulSoup(res.html, "html.parser")
                for tag in soup.find_all("a", href=True):
                    full = urljoin(url, tag["href"])
                    parsed = urlparse(full)
                    if parsed.netloc == urlparse(start_url).netloc:
                        norm = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if (
                            norm not in visited
                            and norm not in to_visit
                            and not is_excluded(norm)
                        ):
                            to_visit.add(norm)
                            discovered.add(norm)

    log_progress(
        progress_file, 80, status="discovery done", url=start_url
    )  # URL consistent doorgeven
    return discovered


async def crawl_all(urls, max_concurrent, progress_file, start_url):
    date = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join("output", date)
    os.makedirs(out_dir, exist_ok=True)

    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig(
        css_selector="main, article, section",
        excluded_selector=".cookie, .consent, .banner",
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()
        ),
    )

    results_by_domain = defaultdict(dict)
    total = len(urls)
    done = 0
    success = 0
    fail = 0

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = [
                crawler.arun(url, crawl_config, session_id=f"batch_{i+j}")
                for j, url in enumerate(batch)
            ]

            for url, task in zip(
                batch, await asyncio.gather(*tasks, return_exceptions=True)
            ):
                try:
                    if isinstance(task, Exception):
                        raise task
                    res = task

                    domain = urlparse(url).netloc
                    output_filepath = os.path.join(out_dir, f"{domain}.json")

                    if os.path.exists(output_filepath):
                        with open(output_filepath, "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                            if url in existing_data:
                                if existing_data[url]["hash"] == hashlib.sha256(
                                    res.markdown.encode()).hexdigest():
                                    print(f"🔄 {url} al verwerkt, overslaan")
                                    continue

                    if res.success and res.markdown.fit_markdown:
                        summary = clean_text(res.markdown.fit_markdown)
                        
                        results_by_domain[domain].append(
                            {
                                "url": url,
                                "titel": url.rstrip("/").split("/")[-1] or domain,
                                "samenvatting": summary,
                                "hash": hashlib.sha256(res.markdown.encode()).hexdigest(),
                            }
                        )
                        success += 1
                    else:
                        fail += 1
                except Exception:
                    fail += 1
                finally:
                    done += 1
                    progress = 80 + int((done / total) * 20) if total else 80
                    log_progress(
                        progress_file,
                        progress,
                        "scraping",
                        done,
                        total,
                        success,
                        fail,
                        url=start_url,  # URL consistent doorgeven
                    )

    for domain, items in results_by_domain.items():
        with open(os.path.join(out_dir, f"{domain}.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    log_progress(
        progress_file, 100, "done", done, total, success, fail, url=start_url
    )  # URL consistent doorgeven


async def run_scrape(url: str, job_id: str):
    progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
    log_progress(progress_file, 0, "starting", url=url)


    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        try:
            links = await collect_internal_urls(
                crawler, url, MAX_CONCURRENT, progress_file
            )
            await crawl_all(list(links), MAX_CONCURRENT, progress_file, url)
        except Exception as e:
            log_progress(
                progress_file, 100, f"error: {str(e)}", url=url
            )  # URL consistent doorgeven
            raise


def main(url: str, job_id: str):
    asyncio.run(run_scrape(url, job_id))
