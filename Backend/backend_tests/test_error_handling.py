import os, sys
import shutil
import pytest
from unittest.mock import patch

# Get the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add parent directory to sys.path
sys.path.append(parent_dir)

from Crawlscraper import log_error, crawl_parallel


# Mock classes for simulating crawl results
class DummyMarkdown:
    """Mock markdown object representing extracted content"""
    def __init__(self, text):
        self.fit_markdown = text


class DummyResult:
    """Mock result object representing a successful crawl response"""
    def __init__(self, markdown):
        self.success = True
        self.markdown = DummyMarkdown(markdown)


@pytest.fixture(autouse=True)
def cleanup_testoutput():
    """
    Fixture to clean up test output before each test
    
    This ensures each test starts with a clean environment by removing
    any existing testoutput directory and its contents.
    """
    if os.path.exists("testoutput"):
        shutil.rmtree("testoutput")


def test_log_error_creates_log_file_in_testoutput():
    """
    Test that log_error function correctly creates and writes to log files
    
    This test verifies:
    1. Log directory is created if it doesn't exist
    2. Error information is written to the log file
    3. Log entries contain expected information (URL, error message, timestamp)
    """
    url = "https://example.com/test"
    error = Exception("Testfout")

    # Use a separate test output directory
    log_dir = os.path.join("testoutput", "logs")
    log_error(url, error, log_dir=log_dir)

    # Verify log file was created
    log_path = os.path.join(log_dir, "errors.log")
    assert os.path.exists(log_path)

    # Check that the log entry contains the correct information
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert url in content
        assert "Testfout" in content
        assert "[" in content  # Timestamp should be present


@pytest.mark.asyncio
async def test_crawl_parallel_handles_exceptions():
    """
    Test that crawl_parallel properly handles and logs exceptions
    
    This test simulates a mixed scenario where some URLs succeed and others fail,
    verifying that:
    1. Successful crawls continue despite failures
    2. Exceptions are properly caught and logged
    3. Error details are written to the log file
    4. The process doesn't crash when individual URLs fail
    """
    urls = [
        "https://in-gouda.nl/geslaagd",   # This will succeed
        "https://in-gouda.nl/timeout",    # This will fail
        "https://in-gouda.nl/404",        # This will also fail
    ]

    # Mock async crawl function: only 'geslaagd' succeeds, others fail
    async def fake_arun(url, config, session_id=None):
        if "geslaagd" in url:
            return DummyResult("# Titel\nInhoud van de pagina.")
        else:
            raise Exception("Simulated crawl failure")

    # Patch AsyncWebCrawler to avoid making real HTTP requests
    with patch("Crawlscraper.AsyncWebCrawler") as MockCrawler:
        mock = MockCrawler.return_value.__aenter__.return_value
        mock.arun.side_effect = fake_arun

        # Run the parallel crawl with our test log directory
        test_log_dir = os.path.join("testoutput", "logs")
        await crawl_parallel(urls, max_concurrent=3, log_dir=test_log_dir)

        # Verify that errors were logged
        log_file = os.path.join(test_log_dir, "errors.log")
        assert os.path.exists(log_file)

        # Check that the correct errors are logged
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
            assert "timeout" in log_content     # Failed URL should be logged
            assert "404" in log_content         # Failed URL should be logged
            assert "Simulated crawl failure" in log_content  # Error message should be logged
