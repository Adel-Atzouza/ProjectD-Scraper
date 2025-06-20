import scrapy
from scrapy_playwright.page import PageMethod


class VerhuurSpider(scrapy.Spider):
    name = "verhuur_buitensport"
    start_urls = ["https://www.sportpuntgouda.nl/verhuur_2"]

    custom_settings = {
        "FEEDS": {
            "verhuur_locaties.csv": {
                "format": "csv",
                "fields": [
                    "categorie",
                    "sportpark",
                    "pagina_url",
                    "contact_tel",
                    "algemene_contact_email",
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
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "LOG_LEVEL": "WARNING",
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={"playwright": True},
            callback=self.parse_main,
            errback=self.errback_log,
        )

    def parse_main(self, response):
        # Zoek link naar "Buitensport"
        buitensport_url = response.css(
            "a:contains('Buitensport')::attr(href)").get()
        if buitensport_url:
            yield response.follow(
                url=buitensport_url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [PageMethod("wait_for_timeout", 1000)],
                },
                callback=self.parse_buitensport,
                errback=self.errback_log,
            )
        else:
            self.logger.warning(
                "⚠️ Geen link naar Buitensport gevonden op verhuur_2")

    def parse_buitensport(self, response):
        # Lees algemene SPORT•GOUDA-footergegevens
        footer = response.xpath(
            "//div[contains(@class, 'col-md-4') and contains(., 'SPORT•GOUDA')]"
        )
        algemene_email = (
            footer.xpath(".//a[starts-with(@href, 'mailto:')]/text()")
            .get(default="")
            .strip()
        )

        # Klik door naar elk sportpark (linkkaarten)
        for link in response.css(".card a::attr(href)").getall():
            yield response.follow(
                url=link,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [PageMethod("wait_for_timeout", 1000)],
                    "algemene_email": algemene_email,
                },
                callback=self.parse_sportpark,
                errback=self.errback_log,
            )

    def parse_sportpark(self, response):
        pagina_url = response.url
        naam = response.css("h1::text").get(default="").strip()
        tel = response.css("a[href^='tel:']::text").get(default="").strip()
        algemene_email = response.meta.get("algemene_email", "")

        if not naam:
            self.logger.warning(f"⚠️ Geen naam gevonden op {pagina_url}")
        else:
            yield {
                "categorie": "Buitensport",
                "sportpark": naam,
                "pagina_url": pagina_url,
                "contact_tel": tel,
                "algemene_contact_email": algemene_email,
            }

    def errback_log(self, failure):
        self.logger.error(
            f"❌ Fout bij laden van pagina: {failure.request.url} - {repr(failure)}"
        )


# import scrapy
# from scrapy.crawler import CrawlerProcess
# from scrapy_playwright.page import PageMethod

# class VerhuurSpider(scrapy.Spider):
#     name = "verhuur_buitensport"
#     start_urls = ["https://www.sportpuntgouda.nl/verhuur_2"]

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
#         "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
#         "LOG_LEVEL": "INFO",
#     }

#     def start_requests(self):
#         yield scrapy.Request(
#             url="https://www.sportpuntgouda.nl/verhuur_2",
#             meta={
#                 "playwright": True,
#                 "playwright_page_methods": [
#                     PageMethod("click", "a[href='/sportparken']"),
#                     PageMethod("wait_for_timeout", 1000)
#                 ]
#             },
#             callback=self.parse_sportparken
#         )

#     def parse_sportparken(self, response):
#         pagina_url = response.url
#         contact_tekst = response.css('a[href^="tel:"]::text').get()


#         ## algemene_email = response.css("a[href^='mailto:']::text").get(default="").strip()

#         footer_block = response.xpath("//div[contains(@class, 'col-md-4') and contains(., 'SPORT•GOUDA')]")
#         algemene_naam = footer_block.xpath(".//strong/text()").get(default="").strip()
#         adresregel = footer_block.xpath(".//p/br/following-sibling::text()[1]").get(default="").strip()
#         algemene_tel = footer_block.xpath(".//a[starts-with(@href, 'tel:')]/text()").get(default="").strip()
#         algemene_email = footer_block.xpath(".//a[starts-with(@href, 'mailto:')]/text()").get(default="").strip()
#         self.logger.info(f" Miranda-tekst: {contact_tekst}")

#         algemene_contact = f"{algemene_naam}, {adresregel}, {algemene_tel}, {algemene_email}"

#         for card in response.css(".card-stretch-hover"):
#             naam = card.css("h5::text").get(default="").strip()
#             if not naam:
#                 continue

#             yield {
#                 "categorie": "Buitensport",
#                 "sportpark": naam,
#                 "pagina_url": pagina_url,
#                 "contact_tel": contact_tekst,
#                 "algemene_contact_email": algemene_contact
#             }


# # ✅ Start de crawler
# process = CrawlerProcess()
# process.crawl(VerhuurSpider)
# process.start()
