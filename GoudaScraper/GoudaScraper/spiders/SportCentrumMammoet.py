import scrapy
from scrapy_playwright.page import PageMethod


class SportcentrumMammoetSpider(scrapy.Spider):
    name = "sportcentrummammoet_zalen"
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
        "LOG_LEVEL": "WARNING",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [PageMethod("wait_for_timeout", 1000)]
                },
                callback=self.parse_zalen,
                errback=self.errback_log
            )

    def parse_zalen(self, response):
        pagina_url = response.url
        locatie = "Sportcentrum de Mammoet"

        try:
            zalen = response.css(".card-title.text-theme-3::text")
            if not zalen:
                self.logger.warning(f"⚠️ Geen zalen gevonden op {pagina_url}")

            for zaal in zalen:
                zaal_naam = zaal.get().strip()
                if zaal_naam:
                    yield {
                        "categorie": "Binnensport",
                        "locatie": locatie,
                        "pagina_url": pagina_url,
                        "zaal_naam": zaal_naam
                    }
        except Exception as e:
            self.logger.error(f"❌ Fout bij verwerken van {pagina_url}: {e}")

    def errback_log(self, failure):
        self.logger.error(
            f"❌ Pagina mislukt: {failure.request.url} - {repr(failure)}")


# import scrapy
# from scrapy.crawler import CrawlerProcess
# from scrapy_playwright.page import PageMethod

# class SportcentrumMammoetSpider(scrapy.Spider):
#     name = "sportcentrummammoet_zalen"
#     start_urls = ["https://www.sportpuntgouda.nl/sportcentrum-de-mammoet"]

#     custom_settings = {
#         "FEEDS": {
#             "verhuur_locaties.csv": {
#                 "format": "csv",
#                 "fields": ["categorie", "locatie", "pagina_url", "zaal_naam"],
#                 "encoding": "utf8"
#             }
#         },
#         "DOWNLOAD_HANDLERS": {
#             "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#             "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#         },
#         "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
#         "PLAYWRIGHT_BROWSER_TYPE": "chromium",
#         "LOG_LEVEL": "INFO",
#     }

#     def start_requests(self):
#         for url in self.start_urls:
#             yield scrapy.Request(
#                 url=url,
#                 meta={"playwright": True},
#                 callback=self.parse_zalen
#             )

#     def parse_zalen(self, response):
#         pagina_url = response.url
#         locatie = "Sportcentrum de Mammoet"

#         for zaal in response.css(".card-title.text-theme-3::text"):
#             zaal_naam = zaal.get().strip()
#             if zaal_naam:
#                 yield {
#                     "categorie": "Binnensport",
#                     "locatie": locatie,
#                     "pagina_url": pagina_url,
#                     "zaal_naam": zaal_naam
#                 }


# # ✅ Start de crawler
# process = CrawlerProcess()
# process.crawl(SportcentrumMammoetSpider)
# process.start()
