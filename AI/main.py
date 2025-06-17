import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import pprint


def fetch_and_parse(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.get_text()
    except Exception as e:
        return f"Error fetching {url}: {e}"


def get_page(url: str) -> None:
    root = requests.get(url).content
    soup = BeautifulSoup(root, "html.parser")

    links = [
        "https://goudawijzer.nl" + x["href"] for x in soup.find_all("a", href=True)
    ]

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_and_parse, link): link for link in links}
        results = []
        for future in as_completed(future_to_url):
            text = future.result()
            url = future_to_url[future]
            filename = url.split("/")[-1] + ".txt"
            results.append((filename, text))
        for filename, text in results:
            with open("files/" + filename, "w", encoding="utf-8") as f:
                f.write(pprint.pformat(text))
    print("All pages downloaded and saved.")


if __name__ == "__main__":
    root = get_page("https://www.goudawijzer.nl/is/een-vraag-over/wonen-en-huishouden/")
