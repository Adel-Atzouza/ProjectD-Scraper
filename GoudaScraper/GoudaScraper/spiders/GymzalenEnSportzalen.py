import scrapy
from scrapy_playwright.page import PageMethod


class GymzaalSpider(scrapy.Spider):
    name = "gymzalen"
    start_urls = ["https://www.sportpuntgouda.nl/gymzalen-en-sportzalen"]

    custom_settings = {
        "FEEDS": {
            "verhuur_locaties.csv": {
                "format": "csv",
                "fields": [
                    "categorie",
                    "locatie",
                    "pagina_url",
                    "naam_zaal",
                    "adres_en_wijk",
                    "afmetingen",
                    "douches",
                ],
                "encoding": "utf8",
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
                    "playwright_page_methods": [PageMethod("wait_for_timeout", 1000)],
                },
                callback=self.parse_gymzalen,
                errback=self.errback_log,
            )

    def parse_gymzalen(self, response):
        try:
            cards = response.css("div.card-stretch-hover")
            if not cards:
                self.logger.warning(
                    f"⚠️ Geen gymzalen gevonden op {
                        response.url}"
                )

            for card in cards:
                naam = card.css("h5.card-title::text").get(default="").strip()
                paragrafen = card.css("p::text").getall()
                adres_en_wijk = paragrafen[0].strip() if paragrafen else ""
                afmetingen = (
                    card.xpath(
                        ".//strong[contains(text(),'Afmetingen')]/following-sibling::text()[1]"
                    )
                    .get(default="")
                    .strip()
                )
                douches = (
                    card.xpath(
                        ".//strong[contains(text(),'Douches')]/following-sibling::text()[1]"
                    )
                    .get(default="")
                    .strip()
                )

                if not naam:
                    self.logger.warning(
                        "⚠️ Gymzaal zonder naam gevonden, wordt overgeslagen."
                    )
                    continue

                yield {
                    "categorie": "Binnensport",
                    "locatie": "Gymzalen en Sportzalen",
                    "pagina_url": response.url,
                    "naam_zaal": naam,
                    "adres_en_wijk": adres_en_wijk,
                    "afmetingen": afmetingen,
                    "douches": douches,
                }
        except Exception as e:
            self.logger.error(
                f"❌ Fout tijdens verwerken van gymzalen op {
                    response.url}: {e}"
            )

    def errback_log(self, failure):
        self.logger.error(
            f"❌ Fout bij laden van pagina: {failure.request.url} - {repr(failure)}"
        )


# import scrapy
# from scrapy.crawler import CrawlerProcess
# from scrapy_playwright.page import PageMethod

# class GymzaalSpider(scrapy.Spider):
#     name = "gymzalen"
#     start_urls = ["https://www.sportpuntgouda.nl/gymzalen-en-sportzalen"]

#     custom_settings = {
#         "FEEDS": {
#             "verhuur_locaties.csv": {
#                 "format": "csv",
#                 "fields": [
#                     "categorie", "locatie", "pagina_url",
#                     "naam_zaal", "adres_en_wijk", "afmetingen", "douches"
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
#         for url in self.start_urls:
#             yield scrapy.Request(
#                 url=url,
#                 meta={"playwright": True},
#                 callback=self.parse_gymzalen
#             )

#     def parse_gymzalen(self, response):
#         for card in response.css("div.card-stretch-hover"):
#             naam = card.css("h5.card-title::text").get(default="").strip()
#             paragrafen = card.css("p::text").getall()
#             tekst = " ".join(paragrafen).strip()

#             adres_en_wijk = paragrafen[0].strip() if len(paragrafen) > 0 else ""
#             afmetingen = card.xpath(".//strong[contains(text(),'Afmetingen')]/following-sibling::text()[1]").get(default="").strip()
#             douches = card.xpath(".//strong[contains(text(),'Douches')]/following-sibling::text()[1]").get(default="").strip()

#             yield {
#                 "categorie": "Binnensport",
#                 "locatie": "Gymzalen en Sportzalen",
#                 "pagina_url": response.url,
#                 "naam_zaal": naam,
#                 "adres_en_wijk": adres_en_wijk,
#                 "afmetingen": afmetingen,
#                 "douches": douches
#             }


# # ✅ Start de crawler
# process = CrawlerProcess()
# process.crawl(GymzaalSpider)
# process.start()


# import scrapy
# from scrapy.crawler import CrawlerProcess
# from scrapy_playwright.page import PageMethod

# class BinnensportSpider(scrapy.Spider):
#     name = "verhuur_binnensport"
#     start_urls = [
#         "https://www.sportpuntgouda.nl/sportcentrum-de-mammoet",
#         "https://www.sportpuntgouda.nl/sporthal-de-zebra",
#         "https://www.sportpuntgouda.nl/dick-van-dijkhal",
#         "https://www.sportpuntgouda.nl/gymzalen-en-sportzalen",
#         "https://www.sportpuntgouda.nl/groenhovenbad"
#     ]

#     custom_settings = {
#         "FEEDS": {
#             "verhuur_locaties.csv": {
#                 "format": "csv",
#                 "fields": ["categorie", "sportpark", "pagina_url", "contact_tel", "algemene_contact_email"],
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
#                 callback=self.parse_binnensport
#             )

#     def parse_binnensport(self, response):
#         pagina_url = response.url
#         sportpark = response.css("h1::text").get(default="").strip()
#         contact_tel = response.css('a[href^="tel:"]::text').get(default="").strip()

#         # Footer: algemene contactgegevens
#         footer_block = response.xpath("//div[contains(@class, 'col-md-4') and contains(., 'SPORT•GOUDA')]")
#         algemene_naam = footer_block.xpath(".//strong/text()").get(default="").strip()
#         adresregel = footer_block.xpath(".//p/br/following-sibling::text()[1]").get(default="").strip()
#         algemene_tel = footer_block.xpath(".//a[starts-with(@href, 'tel:')]/text()").get(default="").strip()
#         algemene_email = footer_block.xpath(".//a[starts-with(@href, 'mailto:')]/text()").get(default="").strip()
#         algemene_contact = f"{algemene_naam}, {adresregel}, {algemene_tel}, {algemene_email}"

#         yield {
#             "categorie": "Binnensport",
#             "sportpark": sportpark,
#             "pagina_url": pagina_url,
#             "contact_tel": contact_tel,
#             "algemene_contact_email": algemene_contact
#         }


# # ✅ Start de crawler
# process = CrawlerProcess()
# process.crawl(BinnensportSpider)
# process.start()
