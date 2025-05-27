import csv
import subprocess
import pytest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent  
TEST_OUTPUT = PROJECT_DIR / "output.csv"

@pytest.fixture(scope="module", autouse=True)
def run_spider_once():
    if TEST_OUTPUT.exists():
        TEST_OUTPUT.unlink()  

    subprocess.run(
        ["scrapy", "crawl", "testscraper", "-a", "urls=https://www.sportpuntgouda.nl/"],
        check=True,
        cwd=PROJECT_DIR
    )
    yield


def test_output_file_exists():
    assert TEST_OUTPUT.exists(), "output.csv is niet aangemaakt."


def test_output_has_valid_rows():
    with open(TEST_OUTPUT, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) > 0
        for row in reader:
            assert row["url"].startswith("http")
            assert len(row["raw_text"].strip()) > 10


def test_cookie_text_not_present():
    with open(TEST_OUTPUT, encoding="utf-8") as f:
        content = f.read().lower()
        assert "cookieverklaring" not in content
        assert "grecaptcha" not in content


def test_no_duplicates():
    seen_hashes = set()
    with open(TEST_OUTPUT, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            h = hash(row["raw_text"])
            assert h not in seen_hashes, "Dubbele inhoud gevonden!"
            seen_hashes.add(h)
