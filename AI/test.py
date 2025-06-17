import asyncio
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

MAX_CONCURRENT_TASKS = 5

visited = set()
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)


def is_valid_subpath_link(base_url, target_url):
    base_parts = urlparse(base_url)
    target_parts = urlparse(target_url)
    return base_parts.netloc == target_parts.netloc and target_parts.path.startswith(
        base_parts.path)


async def scrape_page(context, url, base_url, to_visit):
    async with semaphore:
        if url in visited:
            return
        print(f"Scraping: {url}")
        try:
            page = await context.new_page()
            await page.goto(url, timeout=30000)
            content = await page.content()
            await page.close()
        except Exception as e:
            print(f"Failed to load {url}: {e}")
            return

        visited.add(url)
        soup = BeautifulSoup(content, "html.parser")

        # Scrape the page content
        if not os.path.exists("files"):
            os.makedirs("files")

        filename = urlparse(url).path.replace("/", "_") + ".txt"

        paragraphs = soup.find_all("p")
        lines = []
        for p in paragraphs:
            line = ""
            for elem in p.descendants:
                if elem.name == "a" and elem.has_attr("href"):
                    href = urljoin(url, elem["href"])
                    link_text = elem.get_text(separator=" ", strip=True)
                    line += f"{link_text} ({href})"
                elif elem.name is None:
                    line += elem.strip()
            if line.strip():
                lines.append(line.strip())
        text = "\n".join(lines)
        with open(f"files/{filename}", "w", encoding="utf-8") as f:
            f.write(text)

        # Find all links on the page

        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            href = href.split("#")[0]
            if is_valid_subpath_link(base_url, href) and href not in visited:
                to_visit.put_nowait(href)


async def main(base_url):
    to_visit = asyncio.Queue()
    await to_visit.put(base_url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        tasks = []
        while not to_visit.empty() or tasks:
            while not to_visit.empty():
                next_url = await to_visit.get()
                task = asyncio.create_task(
                    scrape_page(context, next_url, base_url, to_visit)
                )
                tasks.append(task)

            # wait for some tasks to complete
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            tasks = list(pending)

        await browser.close()

    print("\n✅ All visited pages:")
    for link in visited:
        print(link)


if __name__ == "__main__":
    start_url = "https://www.goudawijzer.nl/is/een-vraag-over"
    asyncio.run(main(start_url))
