import os
import shutil
import pytest
from unittest.mock import patch
from Crawlscraper import log_error, crawl_parallel

# Dummy markdown-resultaat voor geslaagde fake-crawl
class DummyMarkdown:
    def __init__(self, text):
        self.fit_markdown = text

class DummyResult:
    def __init__(self, markdown):
        self.success = True
        self.markdown = DummyMarkdown(markdown)

# ➕ Fixture: verwijder testoutput vóór elke test
@pytest.fixture(autouse=True)
def cleanup_testoutput():
    if os.path.exists("testoutput"):
        shutil.rmtree("testoutput")

# ✅ Test: log_error schrijft correct naar testoutput/logs/
def test_log_error_creates_log_file_in_testoutput():
    url = "https://example.com/test"
    error = Exception("Testfout")

    log_dir = os.path.join("testoutput", "logs")
    log_error(url, error, log_dir=log_dir)

    log_path = os.path.join(log_dir, "errors.log")
    assert os.path.exists(log_path)

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert url in content
        assert "Testfout" in content
        assert "[" in content  # timestamp aanwezig

# ✅ Test: crawl_parallel logt fouten naar testoutput/logs/
@pytest.mark.asyncio
async def test_crawl_parallel_handles_exceptions():
    urls = [
        "https://in-gouda.nl/geslaagd",
        "https://in-gouda.nl/timeout",
        "https://in-gouda.nl/404"
    ]

    async def fake_arun(url, config, session_id=None):
        if "geslaagd" in url:
            return DummyResult("# Titel\nInhoud van de pagina.")
        else:
            raise Exception("Simulated crawl failure")

    with patch("Crawlscraper.AsyncWebCrawler") as MockCrawler:
        mock = MockCrawler.return_value.__aenter__.return_value
        mock.arun.side_effect = fake_arun

        test_log_dir = os.path.join("testoutput", "logs")
        await crawl_parallel(urls, max_concurrent=3, log_dir=test_log_dir)

        log_file = os.path.join(test_log_dir, "errors.log")
        assert os.path.exists(log_file)

        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            assert "timeout" in log_content
            assert "404" in log_content
            assert "Simulated crawl failure" in log_content
