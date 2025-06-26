import sys
import os

# Get the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add parent directory to sys.path
sys.path.append(parent_dir)

from Crawlscraper import collect_internal_urls
import pytest

# Additional path setup for module resolution
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")))


@pytest.mark.asyncio
async def test_collect_internal_urls_filters_domain_correctly():
    """
    Test that collect_internal_urls only includes URLs from the same domain
    
    This test verifies the core domain filtering functionality by providing
    HTML content with both internal and external links, then checking that
    only internal links are included in the results.
    """
    class MockCrawler:
        """Mock crawler that returns predefined HTML content"""
        async def arun(self, url, config, session_id):
            class MockResponse:
                """Mock response containing test HTML with mixed link types"""
                def __init__(self):
                    self.success = True
                    self.html = """
                        <html>
                            <body>
                                <a href="/internal1">Link 1</a>
                                <a href="https://external.com/page">External</a>
                            </body>
                        </html>
                    """

            return MockResponse()

    # Test the function with our mock crawler
    crawler = MockCrawler()
    start_url = "https://example.com"
    result = await collect_internal_urls(crawler, start_url, batch_size=1)
    
    # Verify that internal URLs are included and external URLs are excluded
    assert any("example.com/internal1" in url for url in result)
    assert all("external.com" not in url for url in result)
