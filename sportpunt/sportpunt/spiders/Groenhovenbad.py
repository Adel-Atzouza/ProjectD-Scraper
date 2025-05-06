import scrapy
from scrapy_playwright.page import PageMethod

class GroenhovenbadSpider(scrapy.Spider):
    name = "groenhovenbad"
    start_urls = ["https://www.sportpuntgouda.nl/groenhovenbad"]

    custom_settings = {
        "FEEDS": {
            "verhuur_locaties.csv": {
                "format": "csv",
                "fields": [
                    "categorie", "locatie", "pagina_url",
                    "item_naam", "afmeting", "bijzonderheden", "tarief"
                ],
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
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_page_methods": [PageMethod("wait_for_timeout", 1000)]
            },
            callback=self.parse_groenhovenbad,
            errback=self.errback_log
        )

    def parse_groenhovenbad(self, response):
        pagina_url = response.url
        locatie = "Groenhovenbad"

        try:
            # Deel 1: baden bovenaan
            for naam in response.css("h5.card-title.text-theme-1::text"):
                bad_naam = naam.get().strip()
                if not bad_naam:
                    self.logger.warning(f"⚠️ Lege badnaam gevonden op {pagina_url}")
                    continue

                yield {
                    "categorie": "Binnensport",
                    "locatie": locatie,
                    "pagina_url": pagina_url,
                    "item_naam": bad_naam,
                    "afmeting": "",
                    "bijzonderheden": "",
                    "tarief": ""
                }

            # Deel 2: verhuur-tarieven onderaan
            rows = response.css("table.table-striped tr")
            current_name = ""
            for row in rows:
                name_el = row.css("h5::text").get()
                if name_el:
                    current_name = name_el.strip()
                    continue

                texts = row.css("td::text").getall()
                texts = [t.strip() for t in texts if t.strip()]
                if len(texts) == 2:
                    afm_bijz = texts[0]
                    prijs = texts[1]

                    afmeting = ""
                    bijzonderheden = ""
                    if "Afmeting:" in afm_bijz:
                        delen = afm_bijz.split("Bijzonderheden:")
                        afmeting = delen[0].replace("Afmeting:", "").strip()
                        if len(delen) > 1:
                            bijzonderheden = delen[1].strip()

                    if not current_name:
                        self.logger.warning(f"⚠️ Rij met afmetingen/tarief maar zonder item_naam op {pagina_url}")
                        continue

                    yield {
                        "categorie": "Binnensport",
                        "locatie": locatie,
                        "pagina_url": pagina_url,
                        "item_naam": current_name,
                        "afmeting": afmeting,
                        "bijzonderheden": bijzonderheden,
                        "tarief": prijs
                    }

        except Exception as e:
            self.logger.error(f"❌ Fout bij het verwerken van {pagina_url}: {e}")

    def errback_log(self, failure):
        self.logger.error(f"❌ Fout bij laden van pagina: {failure.request.url} - {repr(failure)}")



# import scrapy
# from scrapy.crawler import CrawlerProcess
# from scrapy_playwright.page import PageMethod

# class GroenhovenbadSpider(scrapy.Spider):
#     name = "groenhovenbad"
#     start_urls = ["https://www.sportpuntgouda.nl/groenhovenbad"]

#     custom_settings = {
#         "FEEDS": {
#             "verhuur_locaties.csv": {
#                 "format": "csv",
#                 "fields": [
#                     "categorie", "locatie", "pagina_url",
#                     "item_naam", "afmeting", "bijzonderheden", "tarief"
#                 ],
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
#         yield scrapy.Request(
#             url=self.start_urls[0],
#             meta={"playwright": True},
#             callback=self.parse_groenhovenbad
#         )

#     def parse_groenhovenbad(self, response):
#         pagina_url = response.url
#         locatie = "Groenhovenbad"

#         # Deel 1: baden bovenaan (via h5.titel in cards)
#         for naam in response.css("h5.card-title.text-theme-1::text"):
#             yield {
#                 "categorie": "Binnensport",
#                 "locatie": locatie,
#                 "pagina_url": pagina_url,
#                 "item_naam": naam.get().strip(),
#                 "afmeting": "",
#                 "bijzonderheden": "",
#                 "tarief": ""
#             }

#         # Deel 2: verhuur-tarieven onderaan
#         rows = response.css("table.table-striped tr")
#         current_name = ""
#         for row in rows:
#             # Titels zoals "Spaardersbad", "Trekfuil"
#             name_el = row.css("h5::text").get()
#             if name_el:
#                 current_name = name_el.strip()
#                 continue

#             texts = row.css("td::text").getall()
#             texts = [t.strip() for t in texts if t.strip()]
#             if len(texts) == 2:
#                 afm_bijz = texts[0]
#                 prijs = texts[1]

#                 afmeting = ""
#                 bijzonderheden = ""
#                 if "Afmeting:" in afm_bijz:
#                     delen = afm_bijz.split("Bijzonderheden:")
#                     afmeting = delen[0].replace("Afmeting:", "").strip()
#                     if len(delen) > 1:
#                         bijzonderheden = delen[1].strip()

#                 yield {
#                     "categorie": "Binnensport",
#                     "locatie": locatie,
#                     "pagina_url": pagina_url,
#                     "item_naam": current_name,
#                     "afmeting": afmeting,
#                     "bijzonderheden": bijzonderheden,
#                     "tarief": prijs
#                 }


# # ✅ Start de crawler
# process = CrawlerProcess()
# process.crawl(GroenhovenbadSpider)
# process.start()