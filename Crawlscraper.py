import os
import re
import json
import asyncio
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Set
from datetime import datetime
from collections import defaultdict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

START_URLS = ["https://in-gouda.nl/"]
MAX_CONCURRENT = 15
EXCLUDE_EXTENSIONS = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".rar",
]

# ------------------ Logging ------------------


def log_error(url: str, error: Exception, log_dir: str = "output/logs"):
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "errors.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] ERROR @ {url}: {str(error)}\n")


# ------------------ Helpers ------------------


# Controleer of de URL eindigt op een uitgesloten extensie
def is_excluded(url: str) -> bool:
    return any(url.lower().endswith(ext) for ext in EXCLUDE_EXTENSIONS)


# Maak de markdown-tekst schoon
def clean_text(markdown: str) -> str:
    markdown = re.sub(
        r"(?m)^.*\|.*\|.*$", "", markdown
        # Verwijder regels die tabellen bevatten (regels met minimaal twee
        # pipes)
    )
    markdown = re.sub(
        r"\[(.*?)\]\([^)]+\)", r"\1", markdown
    )  # Verwijder markdown-links, alleen de zichtbare tekst blijft over
    markdown = re.sub(
        r"#+ ", "", markdown
    )  # Verwijder markdown headers (regels die beginnen met #)
    markdown = re.sub(
        r"\n{3,}", "\n\n", markdown.strip()
    )  # Vervang drie of meer nieuwe regels door maximaal twee nieuwe regels
    sentences = re.split(
        r"(?<=[.!?]) +", markdown
    )  # Splits de tekst op in losse zinnen
    return " ".join(
        sentences[:5]
        # Geef maximaal de eerste vijf zinnen terug, samengevoegd tot één
        # string
    ).strip()


# # Haal de titel uit de markdown (eerste regel die met '# ' begint)
# def extract_title(markdown: str) -> str:
#     for line in markdown.splitlines():
#         # Als de regel met '# ' begint, neem de rest van de regel als titel
#         if line.startswith("# "):
#             return line[2:].strip()
#     # Als geen titel gevonden, geef standaardtekst terug
#     return "Geen titel gevonden"

# ------------------ URL-verkenning ------------------


# Verzamelt alle interne URLs vanaf een start-URL binnen hetzelfde domein
async def collect_internal_urls(
        crawler,
        start_url: str,
        batch_size=15) -> Set[str]:
    # Zet met te bezoeken URLs, reeds bezochte URLs en gevonden interne URLs
    to_visit = set([start_url])
    visited = set()
    discovered = set()

    # Configuratie voor de crawler (geen cache, standaard markdown)
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator())
    # Unieke sessie-ID voor deze crawl
    session_id = f"discovery_{urlparse(start_url).netloc}"

    # Zolang er nog URLs te bezoeken zijn
    while to_visit:
        current_batch = list(to_visit)[
            :batch_size
        ]  # Pak een batch van URLs om tegelijk te bezoeken
        to_visit.difference_update(
            current_batch
        )  # Haal deze batch uit de te bezoeken set
        # Voeg deze batch toe aan de bezochte set
        visited.update(current_batch)

        print(f"\n [Batch discovery] {len(discovered) + 1} URLs")
        tasks = [
            crawler.arun(url, crawl_config, session_id=session_id)
            for url in current_batch
        ]  # Start crawl-taken voor alle URLs in de batch
        results = await asyncio.gather(
            *tasks, return_exceptions=True
        )  # Wacht tot alle taken klaar zijn (ook als er fouten zijn)

        # Verwerk de resultaten van de batch
        for url, res in zip(current_batch, results):
            if isinstance(
                res, Exception
            ):  # Log en sla fout over als er een exception was
                print(f" ❌ {url}: {res}")
                log_error(url, res)  # gebruikt default output/logs
                continue

            if (
                res.success and res.html
            ):  # Alleen verder als crawl succesvol was en HTML is opgehaald
                soup = BeautifulSoup(res.html, "html.parser")
                for tag in soup.find_all(
                    "a", href=True
                ):  # Zoek alle <a href="..."> links op de pagina
                    href = tag["href"]
                    # Maak van relatieve links absolute URLs
                    full = urljoin(url, href)
                    parsed = urlparse(full)
                    if (
                        parsed.netloc == urlparse(start_url).netloc
                    ):  # Alleen interne links (zelfde domein) toevoegen
                        # Normaliseer de URL (zonder query/fragment)
                        norm = parsed.scheme + "://" + parsed.netloc + parsed.path
                        # Voeg toe als nog niet bezocht, niet in to_visit en
                        # niet uitgesloten
                        if (
                            not is_excluded(norm)
                            and norm not in visited
                            and norm not in to_visit
                        ):
                            to_visit.add(norm)
                            discovered.add(norm)

    # Geef alle gevonden interne URLs terug
    return discovered


# ------------------ Crawling & Samenvatten ------------------


# Crawlt meerdere URLs parallel, maakt samenvattingen en slaat per domein op
async def crawl_parallel(
    urls: List[str], max_concurrent: int, log_dir: str = "output/logs"
):
    print("\n=== Parallel Crawling gestart ===")

    # Maak output directory aan op basis van de datum
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join("output", date_str)
    os.makedirs(output_dir, exist_ok=True)

    # Stel browser en crawl-configuratie in
    browser_config = BrowserConfig(headless=True)
    crawl_config = CrawlerRunConfig(
        css_selector="main, article, section",
        excluded_selector=".cookie, .cookie-banner, .consent, .privacy",
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter()
        ),
        stream=False,
    )

    # Resultaten per domein opslaan
    domain_results = defaultdict(list)

    # Start de asynchrone webcrawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i in range(
            0, len(urls), max_concurrent
        ):  # Verwerk de URLs in batches van max_concurrent
            batch = urls[i: i + max_concurrent]
            tasks = [
                crawler.arun(url, crawl_config, session_id=f"batch_{i + j}")
                for j, url in enumerate(batch)
            ]  # Maak taken aan voor alle URLs in de batch
            results_batch = await asyncio.gather(
                *tasks, return_exceptions=True
            )  # Wacht tot alle taken klaar zijn (ook als er fouten zijn)

            # Verwerk de resultaten van de batch
            for url, res in zip(batch, results_batch):
                # Log en sla fout over als er een exception was
                if isinstance(res, Exception):
                    print(f" ❌ Exception @ {url}: {res}")
                    log_error(url, res, log_dir=log_dir)
                    continue

                # Haal de markdown uit het resultaat
                markdown = res.markdown.fit_markdown
                # Sla over als er geen markdown is
                if not markdown:
                    continue

                # Maak een samenvatting van de markdown
                summary = clean_text(markdown)
                # Titel is het laatste stuk van de URL of de domeinnaam
                # title = extract_title(markdown)

                # Bouw het resultaat op
                result = {
                    "url": url,
                    "titel": url.rstrip("/").split("/")[-1] or urlparse(url).netloc,
                    "samenvatting": summary,
                }

                # Voeg het resultaat toe aan het juiste domein
                netloc = urlparse(url).netloc
                domain_results[netloc].append(result)
                print(f" ✅ {url} toegevoegd aan {netloc}")

    # Schrijf de resultaten per domein weg naar een JSON-bestand
    for domain, results in domain_results.items():
        filepath = os.path.join(output_dir, f"{domain}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📦 Samenvatting opgeslagen per domein in map: {output_dir}")


# ------------------ Entry point ------------------


async def main():
    browser_config = BrowserConfig(headless=True)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        all_urls = set()
        for start_url in START_URLS:
            print(f"\n🔎 Interne links verzamelen vanaf: {start_url}")
            found_urls = await collect_internal_urls(
                crawler, start_url, batch_size=MAX_CONCURRENT
            )
            print(f"🔗 {len(found_urls)} gevonden vanaf {start_url}")
            all_urls.update(found_urls)

        print(f"\n🌐 Totaal unieke interne URLs: {len(all_urls)}")
        # log_dir optioneel
        await crawl_parallel(list(all_urls), MAX_CONCURRENT)

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
