import scrapy
from scrapy_playwright.page import PageMethod


class SportAanbiedersSpider(scrapy.Spider):
    name = "sportaanbieders"
    start_urls = [
        "https://www.sportpuntgouda.nl/sporten-in-gouda"
    ]

    custom_settings = {
        "FEEDS": {
            "sportaanbieders_gouda.csv": {
                "format": "csv",
                "fields": ["soort_sport", "sportaanbieder", "website"],
                "encoding": "utf8"
            }
        },
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "LOG_LEVEL": "WARNING",
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("evaluate", "() => { document.querySelectorAll('.accordion .card-header').forEach(e => e.click()); }"),
                    PageMethod("wait_for_timeout", 1000)
                ],
            },
            callback=self.parse_sportaanbieders,
            errback=self.errback_log
        )

    def parse_sportaanbieders(self, response):
        try:
            cards = response.css(".accordion .card")
            if not cards:
                self.logger.warning(f"⚠️ Geen sportkaarten gevonden op {response.url}")

            vorige_soort = None

            for card in cards:
                rows = card.css("table tr")

                for row in rows:
                    cols = row.css("td")
                    if len(cols) < 3:
                        continue

                    soort_sport = cols[0].css("::text").get(default="").strip()
                    sportaanbieder = cols[1].css("::text").get(default="").strip()
                    website = cols[2].css("a::attr(href)").get(default="").strip()

                    if not sportaanbieder and not website:
                        continue

                    if soort_sport:
                        vorige_soort = soort_sport
                    else:
                        soort_sport = vorige_soort

                    if not soort_sport or not sportaanbieder:
                        self.logger.debug("⏭️ Rij overgeslagen wegens ontbrekende gegevens.")
                        continue

                    yield {
                        "soort_sport": soort_sport,
                        "sportaanbieder": sportaanbieder,
                        "website": website
                    }

        except Exception as e:
            self.logger.error(f"❌ Fout bij het verwerken van {response.url}: {e}")

    def errback_log(self, failure):
        self.logger.error(f"❌ Fout bij laden van pagina: {failure.request.url} - {repr(failure)}")
