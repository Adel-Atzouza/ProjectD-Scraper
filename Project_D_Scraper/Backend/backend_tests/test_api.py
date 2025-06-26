import pytest
import requests
import time
import os
from urllib.parse import urlparse
from Project_D_Scraper.Backend.backend_tests.helper import extract_phone_number

BASE_URL = "http://localhost:8000"

##############
# API TESTS  #
##############

def test_get_websites_structure():
    response = requests.get(f"{BASE_URL}/websites")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
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
    assert r1.status_code == 200
    assert r2.status_code == 200

def test_delete_existing_website_by_url():
    url = "https://delete-me.com"
    requests.post(f"{BASE_URL}/websites", json={"url": url})
    delete = requests.delete(f"{BASE_URL}/websites", params={"url": url})
    assert delete.status_code == 200
    data = delete.json()
    assert data["url"] == url

def test_delete_non_existing_website_by_url():
    response = requests.delete(f"{BASE_URL}/websites", params={"url": "https://nonexistent.com"})
    assert response.status_code == 404

def test_delete_existing_website_by_id():
    post = requests.post(f"{BASE_URL}/websites", json={"url": "https://delete-by-id.com"})
    website_id = post.json()["id"]
    delete = requests.delete(f"{BASE_URL}/websites/{website_id}")
    assert delete.status_code == 200
    data = delete.json()
    assert data["id"] == website_id

def test_delete_non_existing_website_by_id():
    response = requests.delete(f"{BASE_URL}/websites/99999999")
    assert response.status_code == 404

def test_start_scrape_valid_url():
    url = "https://scrape-me.com"
    requests.post(f"{BASE_URL}/websites", json={"url": url})
    response = requests.post(f"{BASE_URL}/start-scrape", json={"urls": [url]})
    assert response.status_code == 200
    jobs = response.json()["jobs"]
    assert isinstance(jobs, list)
    assert "job_id" in jobs[0] and isinstance(jobs[0]["job_id"], str)

def test_start_scrape_unknown_url():
    response = requests.post(f"{BASE_URL}/start-scrape", json={"urls": ["https://not-allowed.com"]})
    assert response.status_code == 400
    assert "URL not in website list" in response.text

def test_scrape_progress_valid_job():
    url = "https://track-me.com"
    requests.post(f"{BASE_URL}/websites", json={"url": url})
    response = requests.post(f"{BASE_URL}/start-scrape", json={"urls": [url]})
    job_id = response.json()["jobs"][0]["job_id"]
    time.sleep(0.3)  # Wait a bit for progress file to update
    progress = requests.get(f"{BASE_URL}/scrape-progress/{job_id}")
    assert progress.status_code == 200
    data = progress.json()
    assert "progress" in data and "status" in data

def test_scrape_progress_unknown_job():
    response = requests.get(f"{BASE_URL}/scrape-progress/unknownjob123")
    assert response.status_code == 404

def test_cors_headers():
    headers = {"Origin": "http://localhost:3000"}
    response = requests.options(f"{BASE_URL}/websites", headers=headers)
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

###################
# UTILITY TESTS   #
###################

@pytest.mark.parametrize("html,expected", [
    ("<div>Contact: 06-12345678</div>", "06-12345678"),
    ("<div>Geen telefoonnummer aanwezig</div>", None),
    ("<span>Bel: +31 6 12345678</span>", "+31 6 12345678"),
    ("Mobiel: 0612345678", "0612345678"),
    ("<div>No phone</div>", None),
    ("<div>Telefoon: 06 23456789</div>", "06 23456789"),
])
def test_extract_phone_number(html, expected):
    assert extract_phone_number(html) == expected