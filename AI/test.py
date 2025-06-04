from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

def is_valid_subpath_link(base_url, target_url):
    base_parts = urlparse(base_url)
    target_parts = urlparse(target_url)
    
    return (
        base_parts.netloc == target_parts.netloc and
        target_parts.path.startswith(base_parts.path)
    )

def scrape_links(base_url):
    session = HTMLSession()
    visited = set()
    to_visit = deque([base_url])

    while to_visit:
        url = to_visit.popleft()
        if url in visited:
            continue

        print(f"Scraping: {url}")
        try:
            response = session.get(url)
            response.html.render(timeout=20)
        except Exception as e:
            print(f"Failed to render {url}: {e}")
            continue

        visited.add(url)
        soup = BeautifulSoup(response.html.html, 'html.parser')

        for link_tag in soup.find_all('a', href=True):
            full_url = urljoin(url, link_tag['href'])
            if is_valid_subpath_link(base_url, full_url) and full_url not in visited:
                to_visit.append(full_url)

    print("\nAll visited pages:")
    for link in visited:
        print(link)

if __name__ == "__main__":
    start_url = "https://example.com/start/"  # Replace with your actual starting path
    scrape_links(start_url)
