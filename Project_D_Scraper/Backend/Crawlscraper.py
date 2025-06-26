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

# Configuration constants
PROGRESS_FOLDER = "progress"  # Directory for progress tracking files
MAX_CONCURRENT = 15          # Maximum concurrent crawling operations


async def collect_internal_urls(
    crawler, start_url: str, batch_size: int, progress_file: str
):
    """
    Discover all internal URLs from a starting website
    
    This function performs a breadth-first crawl to find all internal links
    within the same domain as the starting URL. It processes URLs in batches
    for efficient concurrent processing.
    
    Args:
        crawler: AsyncWebCrawler instance for making requests
        start_url: The starting URL to begin discovery from
        batch_size: Number of URLs to process concurrently in each batch
        progress_file: Path to file for logging progress updates
        
    Returns:
        set: Collection of discovered internal URLs
    """
    to_visit = set([start_url])  # URLs queued for visiting
    visited = set()              # URLs already processed
    discovered = set()           # All discovered internal URLs
    
    # Configure crawler for link discovery
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,  # Always fetch fresh content
        markdown_generator=DefaultMarkdownGenerator()
    )
    session_id = f"discovery_{urlparse(start_url).netloc}"

    # Process URLs in batches until none remain
    while to_visit:
        # Take a batch of URLs to process
        batch = list(to_visit)[:batch_size]
        to_visit.difference_update(batch)
        visited.update(batch)

        # Calculate and log progress (discovery phase: 0-80%)
        total = len(to_visit) + len(visited)
        progress = int((len(visited) / total) * 80) if total else 0
        log_progress(
            progress_file, progress, status="discovering", url=start_url
        )

        # Crawl all URLs in the current batch concurrently
        tasks = [
            crawler.arun(url, crawl_config, session_id=session_id) for url in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and extract new links
        for url, res in zip(batch, results):
            if isinstance(res, Exception):
                continue
            if res.success and res.html:
                soup = BeautifulSoup(res.html, "html.parser")
                # Extract all anchor tags with href attributes
                for tag in soup.find_all("a", href=True):
                    full = urljoin(url, tag["href"])  # Convert relative to absolute URL
                    parsed = urlparse(full)
                    
                    # Only include URLs from the same domain
                    if parsed.netloc == urlparse(start_url).netloc:
                        # Normalize URL (remove query params and fragments)
                        norm = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if (
                            norm not in visited
                            and norm not in to_visit
                            and not is_excluded(norm)  # Skip excluded file types
                        ):
                            to_visit.add(norm)
                            discovered.add(norm)

    # Log completion of discovery phase
    log_progress(
        progress_file, 80, status="discovery done", url=start_url
    )
    return discovered


def log_error(url: str, error: Exception, log_dir: str = "output/logs"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "errors.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] ERROR @ {url}: {str(error)}\n")


async def crawl_all(urls, max_concurrent, progress_file, start_url):
    """
    Crawl all discovered URLs and extract content
    
    This function processes all discovered URLs to extract and save their content.
    It includes duplicate detection using content hashing and organizes output by domain.
    
    Args:
        urls: List of URLs to crawl and extract content from
        max_concurrent: Maximum number of concurrent crawling operations
        progress_file: Path to file for logging progress updates
        start_url: Original starting URL (for consistent progress logging)
    """
    # Create output directory organized by date
    date = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join("output", date)
    os.makedirs(out_dir, exist_ok=True)

    # Configure browser and crawler settings
    browser_config = BrowserConfig(headless=True)  # Run in headless mode
    crawl_config = CrawlerRunConfig(
        css_selector="main, article, section",  # Focus on main content areas
        excluded_selector=".cookie, .consent, .banner",  # Skip irrelevant elements
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()  # Remove low-value content
        ),
    )

    # Initialize tracking variables
    results_by_domain = defaultdict(list)  # Group results by domain
    total = len(urls)
    done = 0      # Number of URLs processed
    success = 0   # Number of successful extractions
    fail = 0      # Number of failed extractions

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Process URLs in batches for memory efficiency
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            
            # Create concurrent tasks for the current batch
            tasks = [
                crawler.arun(url, crawl_config, session_id=f"batch_{i+j}")
                for j, url in enumerate(batch)
            ]

            # Process results as they complete
            for url, task in zip(
                batch, await asyncio.gather(*tasks, return_exceptions=True)
            ):
                try:
                    # Handle exceptions from failed requests
                    if isinstance(task, Exception):
                        raise task
                    res = task
                    
                    # Process successful responses with content
                    if res.success and res.markdown.fit_markdown:
                        # Clean and summarize the extracted content
                        summary = clean_text(res.markdown.fit_markdown)
                        domain = urlparse(url).netloc

                        # Check for duplicate content using hash comparison
                        output_file = os.path.join("hashes.json")
                        if os.path.exists(output_file):
                            with open(output_file, "r", encoding="utf-8") as f:
                                existing_data = json.load(f)

                                # Skip if content already exists and is identical
                                if domain in existing_data:
                                    if url in existing_data[domain]:
                                        existing_hash = existing_data[domain][url]["hash"]
                                        current_hash = hashlib.sha256(summary.encode()).hexdigest()
                                        if existing_hash == current_hash:
                                            print(f"Skipping {url} - already exists")
                                            continue

                        # Store extracted content organized by domain
                        results_by_domain[domain].append(
                            {
                                "url": url,
                                "titel": url.rstrip("/").split("/")[-1] or domain,  # Use last path segment as title
                                "samenvatting": summary,
                            }
                        )

                        # Update hash database to track processed content
                        with open("hashes.json", "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                        
                        with open("hashes.json", "w", encoding="utf-8") as f:
                            if domain not in existing_data:
                                existing_data[domain] = {}
                            
                            # Store content hash and timestamp
                            existing_data[domain][url] = {
                                "hash": hashlib.sha256(summary.encode()).hexdigest(),
                                "timestamp": datetime.now().isoformat(),
                            }
                            
                            json.dump(existing_data, f, indent=2, ensure_ascii=False)
                        success += 1
                    else:
                        fail += 1
                except Exception:
                    fail += 1
                finally:
                    # Update progress tracking (scraping phase: 80-100%)
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
                        url=start_url,
                    )

    # Save results organized by domain
    for domain, items in results_by_domain.items():
        with open(os.path.join(out_dir, f"{domain}.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    # Log completion of entire scraping process
    log_progress(
        progress_file, 100, "done", done, total, success, fail, url=start_url
    )


async def run_scrape(url: str, job_id: str):
    """
    Main scraping orchestration function
    
    This function coordinates the entire scraping process for a given URL.
    It performs both URL discovery and content extraction phases.
    
    Args:
        url: The starting URL to scrape
        job_id: Unique identifier for this scraping job
        
    Raises:
        Exception: If any error occurs during the scraping process
    """
    progress_file = os.path.join(PROGRESS_FOLDER, f"{job_id}.json")
    log_progress(progress_file, 0, "starting", url=url)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        try:
            # Phase 1: Discover all internal URLs
            links = await collect_internal_urls(
                crawler, url, MAX_CONCURRENT, progress_file
            )
            # Phase 2: Extract content from all discovered URLs
            await crawl_all(list(links), MAX_CONCURRENT, progress_file, url)
        except Exception as e:
            # Log any errors that occur during scraping
            log_progress(
                progress_file, 100, f"error: {str(e)}", url=url
            )
            raise


# Entry point for command-line execution
if __name__ == "__main__":
    if len(sys.argv) == 3:
        # Run scraper with URL and job ID from command line arguments
        asyncio.run(run_scrape(sys.argv[1], sys.argv[2]))
