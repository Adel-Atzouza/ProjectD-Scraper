import scrapy
from urllib.parse import urlparse
import csv
import hashlib
import re


# Hier kun je nieuwe buttonteksten toevoegen die vaak gebruikt worden voor
# paginering
BUTTON_TEXTS = [
    "load more",
    "see more",
    "show more",
    "next",
    "volgende",
    "meer laden",
    "meer weergeven",
    "next page",
    "→",
    ">>",
    "...",
]

COOKIE_KEYWORDS = [
    "text=Accept all",
    "text=Alle cookies toestaan",
    "text=OK",
    '[id*="cookie"] >> text=Accept',
    '[class*="cookie"] >> text=Akkoord',
    'button:has-text("Toestaan")',
]


class UniversalSpider(scrapy.Spider):
    name = "testscraper"
    allowed_domains = []
    collected_data = []  # In geheugen opslaan voor CSV-output achteraf
    visited_hashes = set()  # Om dubbele pagina's te skippen (hash op inhoud)
    hash_url_map = {}  # Store content_hash -> URL
    idd = 0
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "DEPTH_LIMIT": 10,  # Limiet zodat je geen oneindige loops krijgt bij diepe sites
    }

    def start_requests(self):
        # Init CSV header
        output_file = "output.csv"
        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "raw_text"])
            writer.writeheader()

        urls = getattr(self, "urls", "").split(",")
        for url in urls:
            parsed = urlparse(url)
            self.allowed_domains.append(parsed.netloc)
            yield scrapy.Request(
                url=url,
                callback=self.precheck,
                meta={"original_url": url},
                dont_filter=True,
            )

    def precheck(self, response):
        body = response.xpath("//body//text()[normalize-space()]").getall()
        visible_text = " ".join(body).strip()
        has_script = bool(response.xpath("//script").get())
        has_few_elements = len(response.xpath("//body//*").getall()) < 10

        needs_js = not visible_text or has_script or has_few_elements

        yield scrapy.Request(
            url=response.meta["original_url"],
            meta={
                "playwright": needs_js,
                "playwright_include_page": needs_js,
                "playwright_page_coroutines": (
                    [
                        {"method": "wait_for_load_state", "args": ["networkidle"]},
                        {
                            "method": "evaluate",
                            "args": ["window.scrollTo(0, document.body.scrollHeight)"],
                        },
                    ]
                    if needs_js
                    else []
                ),
            },
            callback=self.parse,
            dont_filter=True,
        )

    async def parse(self, response):
        if response.meta.get("playwright"):
            page = response.meta["playwright_page"]

        # Soms komt er een cookie popup. deze blokeert de scraper om de html te
        # scrapen. clik deze weg.
        for cookie_text in COOKIE_KEYWORDS:
            try:
                locator = page.locator(f'button:has-text("{cookie_text}")')
                if await locator.count() > 0:
                    await locator.first.click(timeout=2000)
                    await page.wait_for_timeout(500)
                    break
            except Exception:
                continue

        # extra check.
        for cookie_text in COOKIE_KEYWORDS:
            try:
                locator = page.locator(f'text="{cookie_text}"')
                if await locator.count() > 0:
                    await locator.first.click(timeout=2000)
                    await page.wait_for_timeout(500)
                    break
            except Exception:
                continue

            # Scroll naar beneden totdat het einde is bereikt
            prev_height = 0
            while True:
                current_height = await page.evaluate("document.body.scrollHeight")
                if current_height == prev_height:
                    break
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(
                    1000
                )  # Hier nog optimaliseren met conditional wait?
                prev_height = current_height

            # Klik op alle bekende knoppen totdat er geen meer zijn
            while True:
                clicked = False
                for text in BUTTON_TEXTS:
                    try:
                        btn = page.locator(f"text={text}")
                        if await btn.count() > 0:
                            await btn.first.click(timeout=2000)
                            await page.wait_for_timeout(1000)
                            clicked = True
                            break  # Één tegelijk om te zorgen dat DOM goed refresht
                    except BaseException:
                        continue
                if not clicked:
                    break

            # Haal nu de volledige pagina-inhoud op
            content = await page.content()
            await page.close()
            response = response.replace(body=content)

        # Haal alle zichtbare tekst uit de body
        raw_text = " ".join(
            response.xpath("//body//text()[normalize-space()]").getall()
        )
        raw_text = " ".join(raw_text.split())
        content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        if content_hash in self.visited_hashes:
            return

        self.visited_hashes.add(content_hash)
        self.hash_url_map[content_hash] = response.url
        # fallback_text = await page.evaluate("document.body.innerText")
        # Dit hierboven is mogelijk een extra optie om alle tekst dat zichtbaar
        # is te pakken.

        with open("output.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "raw_text"])
            irrelevant_patterns = [
                "Cookieverklaring",
                "[#IABV2",
                "var CAPTCHA",
                "Powered by",
                "Toestemming Details",
                "Privacyverklaring",
            ]
            for pattern in irrelevant_patterns:
                raw_text = raw_text.replace(pattern, "")
            raw_text = re.sub(r"\[\#.*?\#\]", "", raw_text)
            raw_text = re.sub(r"var\s+[A-Z_]+\s*=\s*['\"].*?['\"];", "", raw_text)
            raw_text = re.sub(
                r"Cookieverklaring.*?Dataduiker", "", raw_text, flags=re.DOTALL
            )
            writer.writerow({"url": response.url, "raw_text": raw_text})

        with open("urls_visited.csv", "a", newline="", encoding="utf-8") as f:
            self.idd += 1
            writer = csv.DictWriter(f, fieldnames=["id", "url"])

            if f.tell() == 0:
                writer.writeheader()

            writer.writerow({"id": self.idd, "url": response.url})

        # Volg alle interne links (zelfde domein)
        for href in response.xpath("//a/@href").getall():
            absolute_url = response.urljoin(href)
            if self.is_internal(absolute_url):
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.precheck,
                    meta={"original_url": absolute_url},
                    dont_filter=True,  # Anders worden pagina's soms gefilterd door Scrapy zelf
                )

    def is_internal(self, url):
        domain = urlparse(url).netloc
        return any(domain.endswith(allowed) for allowed in self.allowed_domains)

    def closed(self, reason):
        output_file = "output.csv"
        with open(output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "raw_text"])
            writer.writeheader()
            for row in self.collected_data:
                writer.writerow(row)

        # Print hash-to-URL mapping on exit
        print("\nVisited pages (content hash → URL):")
        for h, url in self.hash_url_map.items():
            print(f"{h} -> {url}")

        self.logger.info(f"Saved scraped data to {output_file}")
