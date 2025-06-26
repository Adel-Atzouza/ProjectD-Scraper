import pytest
import asyncio
from unittest.mock import AsyncMock
from urllib.parse import urlparse
import os, sys
# Get the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add parent directory to sys.path
sys.path.append(parent_dir)

from Crawlscraper import collect_internal_urls


# DummyResult simulates the result of a crawl operation
class DummyResult:
    """Mock result object representing a successful crawl response"""
    def __init__(self, success, html):
        self.success = success
        self.html = html


# Test that only internal, non-excluded URLs are collected
@pytest.mark.asyncio
async def test_collect_internal_urls_only_within_domain():
    """
    Test comprehensive domain filtering and URL exclusion
    
    This test verifies that:
    1. Only URLs from the same domain are included
    2. Excluded file types (like .pdf) are filtered out
    3. External domains are completely excluded
    4. Internal paths are properly converted to absolute URLs
    """
    # Simulate HTML with internal and external links, plus excluded files
    html_content = """
        <html>
            <body>
                <a href="/internal-page">Internal</a>
                <a href="https://in-gouda.nl/contact">Also internal</a>
                <a href="https://externedomein.nl/page">External</a>
                <a href="https://in-gouda.nl/file.pdf">Excluded file</a>
            </body>
        </html>
    """

    # Create a mock crawler that always returns the same HTML result
    crawler_mock = AsyncMock()
    crawler_mock.arun.return_value = DummyResult(
        success=True, html=html_content)

    # Call the real function with our fake crawler
    start_url = "https://in-gouda.nl/"
    found_urls = await collect_internal_urls(crawler_mock, start_url, batch_size=5)

    # Verify that only internal, non-excluded URLs are found
    parsed_urls = sorted(found_urls)
    assert all(urlparse(url).netloc == "in-gouda.nl" for url in parsed_urls)
    assert "https://in-gouda.nl/internal-page" in parsed_urls
    assert "https://in-gouda.nl/file.pdf" not in parsed_urls  # Excluded file type
    assert "https://in-gouda.nl/contact" in parsed_urls
    assert all("externedomein.nl" not in url for url in parsed_urls)  # No external domains
    assert all(not url.endswith(".pdf") for url in parsed_urls)       # No PDF files


def test_skip_duplicate_urls():
    """
    Test that duplicate URLs are properly filtered out
    
    This test simulates a common scenario where the same URL appears
    multiple times in a list and verifies that only unique URLs are kept.
    """
    input_urls = [
        "https://in-gouda.nl/contact",
        "https://in-gouda.nl/info",
        "https://in-gouda.nl/contact",  # duplicate
        "https://in-gouda.nl/info",  # duplicate
        "https://in-gouda.nl/home",
    ]

    seen = set()
    output = []

    # Voeg alleen unieke URLs toe aan output
    for url in input_urls:
        if url not in seen:
            seen.add(url)
            output.append(url)

    assert len(output) == 3
    assert "https://in-gouda.nl/contact" in output
    assert "https://in-gouda.nl/info" in output
    assert "https://in-gouda.nl/home" in output


# Test dat visited-tracking werkt en alleen unieke pagina's worden bezocht
def test_skip_duplicate_urls_with_visited_tracking():
    start_url = "https://in-gouda.nl/"
    to_visit = set(
        [
            "https://in-gouda.nl/contact",
            "https://in-gouda.nl/info",
            "https://in-gouda.nl/contact",  # duplicate
            "https://in-gouda.nl/home",
        ]
    )
    visited = set()
    discovered = set()

    # Simuleer batch crawling
    while to_visit:
        current_batch = list(to_visit)[:2]  # pak steeds een batch van 2
        to_visit.difference_update(current_batch)
        visited.update(current_batch)

        for url in current_batch:
            # Simuleer het ontdekken van nieuwe links op deze pagina
            if url == "https://in-gouda.nl/contact":
                new_links = ["https://in-gouda.nl/info"]  # al bekend
            elif url == "https://in-gouda.nl/info":
                new_links = ["https://in-gouda.nl/home"]  # al bekend
            elif url == "https://in-gouda.nl/home":
                new_links = ["https://in-gouda.nl/nieuw"]  # nieuw
            else:
                new_links = []

            # Voeg alleen nieuwe, nog niet bezochte links toe
            for link in new_links:
                if link not in visited and link not in to_visit:
                    to_visit.add(link)
                    discovered.add(link)

    # Verwacht dat we uiteindelijk 4 unieke pagina's kennen
    assert visited == {
        "https://in-gouda.nl/contact",
        "https://in-gouda.nl/info",
        "https://in-gouda.nl/home",
        "https://in-gouda.nl/nieuw",
    }
    assert len(visited) == 4
    assert "https://in-gouda.nl/contact" in visited
    assert "https://in-gouda.nl/nieuw" in visited

    # Extra controle: alle verwachte pagina’s zitten in de uiteindelijke set
    expected_order = [
        "https://in-gouda.nl/contact",
        "https://in-gouda.nl/info",
        "https://in-gouda.nl/home",
        "https://in-gouda.nl/nieuw",
    ]
    actual_order = list(visited)
    for url in expected_order:
        assert url in actual_order
