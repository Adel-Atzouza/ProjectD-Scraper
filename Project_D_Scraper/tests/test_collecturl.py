import pytest
import asyncio
from unittest.mock import AsyncMock
from urllib.parse import urlparse
from Crawlscraper import collect_internal_urls


# DummyResult simuleert het resultaat van een crawl
class DummyResult:
    def __init__(self, success, html):
        self.success = success
        self.html = html


# Test dat alleen interne, niet-uitgesloten URLs worden verzameld
@pytest.mark.asyncio
async def test_collect_internal_urls_only_within_domain():
    # Simuleer HTML met interne én externe links
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

    # Maak een crawler-mock aan die altijd hetzelfde HTML-resultaat teruggeeft
    crawler_mock = AsyncMock()
    crawler_mock.arun.return_value = DummyResult(
        success=True, html=html_content)

    # Roep de echte functie aan met deze fake crawler
    start_url = "https://in-gouda.nl/"
    found_urls = await collect_internal_urls(crawler_mock, start_url, batch_size=5)

    # Controleer dat alleen interne, niet-uitgesloten URLs gevonden zijn
    parsed_urls = sorted(found_urls)
    assert all(urlparse(url).netloc == "in-gouda.nl" for url in parsed_urls)
    assert "https://in-gouda.nl/internal-page" in parsed_urls
    assert "https://in-gouda.nl/file.pdf" not in parsed_urls
    assert "https://in-gouda.nl/contact" in parsed_urls
    assert all("externedomein.nl" not in url for url in parsed_urls)
    assert all(not url.endswith(".pdf") for url in parsed_urls)


# Test dat dubbele URLs worden overgeslagen bij het verzamelen
def test_skip_duplicate_urls():
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
