import pytest
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from  Crawlscraper import is_excluded, clean_markdown_from_soup, collect_internal_urls

# Test voor URL-exclusie op basis van extensies
def test_is_excluded():
    assert is_excluded("https://example.com/file.pdf") is True
    assert is_excluded("https://example.com/image.png") is False
    assert is_excluded("https://example.com/document.docx") is True
    assert is_excluded("https://example.com/page.html") is False

# Test voor clean_markdown_from_soup met cookie-teksten en korte teksten
def test_clean_markdown_from_soup_filters_correct():
    html = """
    <html>
        <body>
            <p>Accepteer cookies alstublieft.</p>
            <h1>Korte</h1>
            <p>Dit is een relevante tekst over een activiteit in Gouda die voldoende lang is.</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = clean_markdown_from_soup(soup)
    assert "cookies" not in result.lower()
    assert "Korte" not in result
    assert "relevante tekst" in result

# Test voor domeincontrole en normalisatie
@pytest.mark.asyncio
async def test_collect_internal_urls_domain_filtering():
    class MockCrawler:
        async def arun(self, url, config, session_id):
            class MockResponse:
                def __init__(self):
                    self.success = True
                    self.html = """
                        <html><body>
                            <a href='/internal1'>Link 1</a>
                            <a href='https://external.com/page'>External</a>
                        </body></html>
                    """
            return MockResponse()

    crawler = MockCrawler()
    start_url = "https://example.com"
    urls = await collect_internal_urls(crawler, start_url, batch_size=1)
    assert any("example.com/internal1" in u for u in urls)
    assert all("external.com" not in u for u in urls)
