import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from Crawlscraper import collect_internal_urls


@pytest.mark.asyncio
async def test_collect_internal_urls_filters_domain_correctly():
    class MockCrawler:
        async def arun(self, url, config, session_id):
            class MockResponse:
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

    crawler = MockCrawler()
    start_url = "https://example.com"
    result = await collect_internal_urls(crawler, start_url, batch_size=1)
    assert any("example.com/internal1" in url for url in result)
    assert all("external.com" not in url for url in result)
