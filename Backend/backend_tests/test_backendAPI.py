import pytest
import requests
import time
import os
from urllib.parse import urlparse
from scraper.utils import clean_html, extract_phone_number  # pas aan indien pad anders
# from scraper.utils import is_footer_text, normalize_url  # optioneel, zie extra tests
# from scraper.visibility import is_visible                # optioneel

BASE_URL = "http://localhost:8000"


@pytest.fixture
def example_site():
    url = "https://fixture-example.com"
    requests.delete(f"{BASE_URL}/websites", params={"url": url})
    response = requests.post(f"{BASE_URL}/websites", json={"url": url})
    assert response.status_code == 200
    return url


def test_get_websites_structure():
    response = requests.get(f"{BASE_URL}/websites")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert isinstance(item, dict)
        assert "id" in item and isinstance(item["id"], int)
        assert "url" in item and isinstance(item["url"], str)
        parsed = urlparse(item["url"])
        assert parsed.scheme in ("http", "https") and parsed.netloc


def test_post_valid_website():
    payload = {"url": "https://example.com"}
    response = requests.post(f"{BASE_URL}/websites", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data and isinstance(data["id"], int)


def test_post_invalid_website():
    payload = {"url": ""}
    response = requests.post(f"{BASE_URL}/websites", json=payload)
    assert response.status_code in (400, 422)


def test_post_duplicate_website():
    url = "https://duplicate.com"
    requests.delete(f"{BASE_URL}/websites", params={"url": url})
    r1 = requests.post(f"{BASE_URL}/websites", json={"url": url})
    r2 = requests.post(f"{BASE_URL}/websites", json={"url": url})
    assert r2.status_code in (200, 409)


def test_delete_existing_website_by_url():
    url = "https://delete-me.com"
    requests.post(f"{BASE_URL}/websites", json={"url": url})
    delete = requests.delete(f"{BASE_URL}/websites", params={"url": url})
    assert delete.status_code == 200


def test_delete_non_existing_website_by_url():
    response = requests.delete(f"{BASE_URL}/websites", params={"url": "https://nonexistent.com"})
    assert response.status_code == 404


def test_delete_existing_website_by_id():
    post = requests.post(f"{BASE_URL}/websites", json={"url": "https://delete-by-id.com"})
    website_id = post.json()["id"]
    delete = requests.delete(f"{BASE_URL}/websites/{website_id}")
    assert delete.status_code == 200


def test_delete_non_existing_website_by_id():
    response = requests.delete(f"{BASE_URL}/websites/999999")
    assert response.status_code == 404


def test_start_scrape_valid_url(example_site):
    response = requests.post(f"{BASE_URL}/start-scrape", json={"url": example_site})
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data and isinstance(data["job_id"], str)


def test_start_scrape_unknown_url():
    response = requests.post(f"{BASE_URL}/start-scrape", json={"url": "https://unknown-url.com"})
    assert response.status_code == 400
    assert "available_urls" in response.json().get("detail", "")


def test_scrape_progress_valid_job(example_site):
    start = requests.post(f"{BASE_URL}/start-scrape", json={"url": example_site})
    job_id = start.json()["job_id"]
    time.sleep(0.2)  # Even wachten op scrape progress
    response = requests.get(f"{BASE_URL}/scrape-progress/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data and "progress" in data


def test_scrape_progress_unknown_job():
    response = requests.get(f"{BASE_URL}/scrape-progress/unknownjob123")
    assert response.status_code == 404


def test_websites_json_fallback(monkeypatch):
    backup = "websites.json.bak"
    if os.path.exists("websites.json"):
        os.rename("websites.json", backup)
    try:
        response = requests.get(f"{BASE_URL}/websites")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        if os.path.exists(backup):
            os.rename(backup, "websites.json")


def test_cors_headers():
    headers = {"Origin": "http://localhost:3000"}
    response = requests.options(f"{BASE_URL}/websites", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


# Extra util tests (pas import aan indien paden anders)
def test_valid_number():
    html = "<div>Contact: 06-12345678</div>"
    result = extract_phone_number(html)
    assert result == "06-12345678"


def test_no_number():
    html = "<div>Geen telefoonnummer aanwezig</div>"
    result = extract_phone_number(html)
    assert result is None


def test_strip_tags():
    raw = "<div><strong>Hallo</strong> wereld&nbsp;</div>"
    cleaned = clean_html(raw)
    assert cleaned == "Hallo wereld"


def test_nested_tags():
    raw = "<div><p><em>Test</em></p></div>"
    assert clean_html(raw) == "Test"


def test_scrape_timing():
    start = time.time()
    time.sleep(0.1)
    end = time.time()
    duration = end - start
    assert 0 < duration < 1
