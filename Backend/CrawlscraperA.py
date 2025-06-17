import os
import sys
import re
import json
import asyncio
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Set
from datetime import datetime
from collections import defaultdict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

PROGRESS_FOLDER = "progress"
MAX_CONCURRENT = 15
EXCLUDE_EXTENSIONS = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".rar",
]


def is_excluded(url: str) -> bool:
    return any(url.lower().endswith(ext) for ext in EXCLUDE_EXTENSIONS)


def clean_text(markdown: str) -> str:
    markdown = re.sub(r"(?m)^.*\|.*\|.*$", "", markdown)
    markdown = re.sub(r"\[(.*?)\]\([^)]+\)", r"\1", markdown)
    markdown = re.sub(r"#+ ", "", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown.strip())
    sentences = re.split(r"(?<=[.!?]) +", markdown)
    return " ".join(sentences[:5]).strip()


async def collect_internal_urls(
    crawler, start_url: str, batch_size: int, progress_file: str
) -> Set[str]:
    to_visit = set([start_url])
    visited = set()
    discovered = set()
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator())
    session_id = f"discovery_{urlparse(start_url).netloc}"

    while to_visit:
        current_batch = list(to_visit)[:batch_size]
        to_visit.difference_update(current_batch)
        visited.update(current_batch)

        visited_count = len(visited)
        to_visit_count = len(to_visit)
        total_estimated = visited_count + to_visit_count
        percent_estimated = (
            int((visited_count / total_estimated)
                * 99) if total_estimated else 0
        )

        with open(progress_file, "w") as f:
            json.dump({"progress": percent_estimated,
                      "status": "discovering"}, f)
            f.flush()
            os.fsync(f.fileno())

        tasks = [
            crawler.arun(url, crawl_config, session_id=session_id)
            for url in current_batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for url, res in zip(current_batch, results):
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
                            not is_excluded(norm)
                            and norm not in visited
                            and norm not in to_visit
                        ):
                            to_visit.add(norm)
                            discovered.add(norm)

    with open(progress_file, "w") as f:
        json.dump({"progress": 99, "status": "discovery done"}, f)

    return discovered


async def crawl_parallel(urls, max_concurrent, progress_file):
    print("\n=== Start parallel crawl ===")
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join("output", date_str)
    os.makedirs(output_dir, exist_ok=True)

    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig(
        css_selector="main, article, section",
        excluded_selector=".cookie, .cookie-banner, .consent, .privacy",
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()
        ),
        stream=False,
    )

    done_count = 0
    success_count = 0
    fail_count = 0
    total_urls = len(urls)
    domain_results = defaultdict(list)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i: i + max_concurrent]
            tasks = [
                crawler.arun(url, crawl_config, session_id=f"batch_{i + j}")
                for j, url in enumerate(batch)
            ]

            for j, task in enumerate(tasks):
                url = batch[j]
                try:
                    res = await task
                    if res.success and res.markdown.fit_markdown:
                        summary = clean_text(res.markdown.fit_markdown)
                        result = {
                            "url": url,
                            "titel": url.rstrip("/").split("/")[-1]
                            or urlparse(url).netloc,
                            "samenvatting": summary,
                        }
                        netloc = urlparse(url).netloc
                        domain_results[netloc].append(result)
                        success_count += 1
                        print(f"✅ {url} toegevoegd aan {netloc}")
                    else:
                        fail_count += 1
                        print(f"⚠️  {url} had geen geldige inhoud")
                except Exception as e:
                    fail_count += 1
                    print(f"❌ {url}: {e}")
                finally:
                    done_count += 1
                    percent_done = int(99 + (done_count / total_urls))
                    with open(progress_file, "w") as f:
                        json.dump(
                            {
                                "progress": percent_done,
                                "status": "crawling",
                                "done": done_count,
                                "total": total_urls,
                                "success": success_count,
                                "failed": fail_count,
                            },
                            f,
                        )
                        f.flush()
                        os.fsync(f.fileno())

    with open(progress_file, "w") as f:
        json.dump(
            {
                "progress": 100,
                "status": "done",
                "done": done_count,
                "total": total_urls,
                "success": success_count,
                "failed": fail_count,
            },
            f,
        )

    for domain, results in domain_results.items():
        filepath = os.path.join(output_dir, f"{domain}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 Done. Data saved in: {output_dir}")


async def run_one_url(url: str, progress_file: str):
    browser_config = BrowserConfig(headless=True)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    try:
        print(f"\n🌐 Crawling site: {url}")
        found_urls = await collect_internal_urls(
            crawler, url, batch_size=MAX_CONCURRENT, progress_file=progress_file
        )
        print(f"🔗 {len(found_urls)} links found for {url}")
        await crawl_parallel(list(found_urls), MAX_CONCURRENT, progress_file)
    finally:
        await crawler.close()


def update_progress(job_id, percent, status="running"):
    progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
    with open(progress_file, "w") as f:
        json.dump({"progress": percent, "status": status}, f)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        url = sys.argv[1]
        job_id = sys.argv[2]
        progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")

        update_progress(job_id, 0, "starting")

        try:
            asyncio.run(run_one_url(url, progress_file))
        except Exception as e:
            with open(progress_file, "w") as f:
                json.dump({"progress": 100, "status": f"error: {str(e)}"}, f)
