import scrapy
from scrapy.crawler import CrawlerProcess


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
        "LOG_LEVEL": "INFO",
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    {
                        "method": "evaluate",
                        "args": ["() => { document.querySelectorAll('.accordion .card-header').forEach(e => e.click()); }"]
                    },
                    {
                        "method": "wait_for_timeout",
                        "args": [1000]
                    }
                ],
            },
            callback=self.parse_sportaanbieders
        )

    def parse_sportaanbieders(self, response):
        cards = response.css(".accordion .card")
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
                    continue

                yield {
                    "soort_sport": soort_sport,
                    "sportaanbieder": sportaanbieder,
                    "website": website
                }


# ✅ Start direct
process = CrawlerProcess()
process.crawl(SportAanbiedersSpider)
process.start()