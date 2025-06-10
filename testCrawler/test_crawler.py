import pytest
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from  Crawlscraper import is_excluded, clean_text, collect_internal_urls

# Test voor URL-exclusie op basis van extensies
def test_is_excluded():
    assert is_excluded("https://example.com/file.pdf") is True
    assert is_excluded("https://example.com/image.png") is False
    assert is_excluded("https://example.com/document.docx") is True
    assert is_excluded("https://example.com/page.html") is False

# Test voor clean_markdown_from_soup met cookie-teksten en korte teksten
def test_clean_text():
    # Test input met markdown elementen die gefilterd moeten worden
    markdown = """
    | Header | Another Header |
    |--------|----------------|
    | Row 1  | Data 1         |
    
    [link text](http://example.com)
    
    # Heading 1
    
    ## Heading 2
    
    Accepteer cookies alstublieft.
    
    Korte tekst.
    
    Dit is een relevante tekst over een activiteit in Gouda. 
    Het heeft meerdere zinnen. Tweede zin. Derde. Vierde. Vijfde. Zesde.
    """
    
    cleaned = clean_text(markdown)
    
    # Assertions
    assert "|" not in cleaned  # Tabellen moeten verwijderd zijn
    assert "[link text]" not in cleaned  # Markdown links moeten verwijderd zijn
    assert "#" not in cleaned  # Markdown headers moeten verwijderd zijn
    assert "cookies" not in cleaned.lower()  # Cookie-teksten moeten verwijderd zijn
    assert "Korte" not in cleaned  # Korte teksten moeten verwijderd zijn
    assert "relevante tekst" in cleaned  # Relevante content moet blijven
    assert len(cleaned.split(". ")) <= 5  # Max 5 zinnen behouden

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
