import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_playwright.page import PageMethod

class SportcentrumMammoetSpider(scrapy.Spider):
    name = "mammoet_zalen"
    start_urls = ["https://www.sportpuntgouda.nl/sportcentrum-de-mammoet"]

    custom_settings = {
        "FEEDS": {
            "verhuur_locaties.csv": {
                "format": "csv",
                "fields": ["categorie", "locatie", "pagina_url", "zaal_naam"],
                "encoding": "utf8"
            }
        },
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "LOG_LEVEL": "INFO",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={"playwright": True},
                callback=self.parse_zalen
            )

    def parse_zalen(self, response):
        pagina_url = response.url
        locatie = "Sportcentrum de Mammoet"

        for zaal in response.css(".card-title.text-theme-3::text"):
            zaal_naam = zaal.get().strip()
            if zaal_naam:
                yield {
                    "categorie": "Binnensport",
                    "locatie": locatie,
                    "pagina_url": pagina_url,
                    "zaal_naam": zaal_naam
                }


# ✅ Start de crawler
process = CrawlerProcess()
process.crawl(SportcentrumMammoetSpider)
process.start()