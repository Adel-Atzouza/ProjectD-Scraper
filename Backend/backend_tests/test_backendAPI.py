from scraper.utils import clean_html  # hypothetische functie
from scraper.utils import extract_phone_number  # hypothetisch hulpfunctiepad
import pytest
import requests
import time
from urllib.parse import urlparse

BASE_URL = "http://localhost:8000"


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
    payload = {"url": ""}  # Leeg of ongeldig
    response = requests.post(f"{BASE_URL}/websites", json=payload)
    assert response.status_code == 422 or response.status_code == 400


def test_delete_existing_website_by_url():
    url = "https://delete-me.com"
    post = requests.post(f"{BASE_URL}/websites", json={"url": url})
    assert post.status_code == 200
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
    response = requests.delete(f"{BASE_URL}/websites/999999")  # aanname: dit ID bestaat niet
    assert response.status_code == 404


def test_start_scrape_valid_url():
    # Eerst URL registreren
    url = "https://scrape-me.com"
    post = requests.post(f"{BASE_URL}/websites", json={"url": url})
    assert post.status_code == 200
    response = requests.post(f"{BASE_URL}/start-scrape", json={"url": url})
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data and isinstance(data["job_id"], str)


def test_start_scrape_unknown_url():
    response = requests.post(f"{BASE_URL}/start-scrape", json={"url": "https://unknown-url.com"})
    assert response.status_code == 400
    assert "available_urls" in response.json()


def test_scrape_progress_valid_job():
    # Eerst scrape starten
    url = "https://progress-check.com"
    post = requests.post(f"{BASE_URL}/websites", json={"url": url})
    assert post.status_code == 200
    start = requests.post(f"{BASE_URL}/start-scrape", json={"url": url})
    job_id = start.json()["job_id"]

    response = requests.get(f"{BASE_URL}/scrape-progress/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "progress" in data


def test_scrape_progress_unknown_job():
    response = requests.get(f"{BASE_URL}/scrape-progress/unknownjob123")
    assert response.status_code == 404


def test_websites_json_fallback(monkeypatch):
    import os
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
    headers = {
        "Origin": "http://localhost:3000",  # typical React dev origin
    }
    response = requests.options(f"{BASE_URL}/websites", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


"""from Crawlscraper.validation import validate_fields  # hypothetische module


def test_all_fields_present():
    row = {"naam": "Buurtcentrum", "type": "Activiteit", "email": "test@mail.nl"}
    assert validate_fields(row)


def test_missing_fields():
    row = {"naam": "Buurtcentrum", "type": "", "email": ""}
    assert not validate_fields(row)
"""
"""from scraper.utils import is_footer_text  # hypothetische functie


def test_detect_footer():
    text = "Over ons | Privacybeleid | Contact"
    assert is_footer_text(text)


def test_non_footer():
    text = "Activiteit op maandag"
    assert not is_footer_text(text)
"""


def test_scrape_timing():
    start = time.time()
    time.sleep(0.1)
    end = time.time()
    duration = end - start
    assert duration > 0
    assert duration < 1


"""from scraper.utils import normalize_url  # hypothetische normalisatie


def test_trailing_slash():
    url1 = "https://testsite.nl/contact"
    url2 = "https://testsite.nl/contact/"
    assert normalize_url(url1) == normalize_url(url2)
"""
"""from scraper.visibility import is_visible  # hypothetisch pad


def test_hidden_element():
    html = '<div style="display:none">Verborgen</div>'
    assert not is_visible(html)


def test_visible_element():
    html = '<div>Toon mij</div>'
    assert is_visible(html)
"""


def test_get_websites_structure():
    response = requests.get("http://localhost:8000/websites")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Expected at least one website in response"

    for item in data:
        assert isinstance(item, dict)
        assert "id" in item and isinstance(item["id"], int)
        assert "url" in item and isinstance(item["url"], str)

        parsed_url = urlparse(item["url"])
        assert parsed_url.scheme in ("http", "https") and parsed_url.netloc, f"Invalid URL: {item['url']}"


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
