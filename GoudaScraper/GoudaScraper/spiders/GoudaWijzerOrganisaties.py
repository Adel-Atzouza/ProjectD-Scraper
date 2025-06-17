import scrapy


class OrganisatiesSpider(scrapy.Spider):
    name = "organisaties"
    start_urls = ["https://www.goudawijzer.nl/is/organisaties?q=&size=1000"]

    custom_settings = {
        "FEEDS": {
            "alle_organisaties.csv": {
                "format": "csv",
                "encoding": "utf8",
            },
        },
        "FEED_EXPORT_FIELDS": [
            "naam",
            "beschrijving",
            "telefoon",
            "email",
            "website",
            "adres",
        ],
        "LOG_LEVEL": "ERROR",
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }

    def parse(self, response):
        organisaties = response.css(".searchResults__contentContainer")

        for org in organisaties:
            naam = org.css(".searchResults__contentHeader a::text").get()
            beschrijving = org.css(
                ".searchResults__content.-textContainer p::text"
            ).get()
            telefoon = org.css('a[href^="tel:"]::text').get()
            email = org.css('a[href^="mailto:"]::attr(href)').re_first(
                r"mailto:(.*)")
            website = org.css("a.external::attr(href)").get()
            straat = org.css("span.-iconAddress::text").get()
            postcode = org.css("span.-locationZip::text").get()
            adres = (
                f"{straat}, {postcode}" if straat and postcode else straat or postcode)

            yield {
                "naam": (naam or "").strip(),
                "beschrijving": (beschrijving or "").strip(),
                "telefoon": (telefoon or "").strip(),
                "email": (email or "").strip(),
                "website": (website or "").strip(),
                "adres": (adres or "").strip(),
            }

        next_page = response.css(
            '.pagination li a[aria-label="Volgende"]::attr(href)'
        ).get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)


# import scrapy
# from scrapy.crawler import CrawlerProcess

# class OrganisatiesSpider(scrapy.Spider):
#     name = 'organisaties'
#     start_urls = ['https://www.goudawijzer.nl/is/organisaties?q=&size=1000']

#     def parse(self, response):
#         organisaties = response.css('.searchResults__contentContainer')

#         for org in organisaties:
#             naam = org.css('.searchResults__contentHeader a::text').get()
#             beschrijving = org.css('.searchResults__content.-textContainer p::text').get()
#             telefoon = org.css('a[href^="tel:"]::text').get()
#             email = org.css('a[href^="mailto:"]::attr(href)').re_first(r'mailto:(.*)')
#             website = org.css('a.external::attr(href)').get()
#             straat = org.css('span.-iconAddress::text').get()
#             postcode = org.css('span.-locationZip::text').get()
#             adres = f"{straat}, {postcode}" if straat and postcode else straat or postcode

#             yield {
#                 'naam': (naam or '').strip(),
#                 'beschrijving': (beschrijving or '').strip(),
#                 'telefoon': (telefoon or '').strip(),
#                 'email': (email or '').strip(),
#                 'website': (website or '').strip(),
#                 'adres': (adres or '').strip(),
#             }

#         # Volgende pagina volgen als die bestaat
#         next_page = response.css('.pagination li a[aria-label="Volgende"]::attr(href)').get()
#         if next_page:
#             yield response.follow(next_page, callback=self.parse)


# # Scrapy CSV export
# process = CrawlerProcess(settings={
#     'FEEDS': {
#         'alle_organisaties.csv': {
#             'format': 'csv',
#             'encoding': 'utf8',
#         },
#     },
#     'FEED_EXPORT_FIELDS': ['naam', 'beschrijving', 'telefoon', 'email', 'website', 'adres'],
#     'LOG_LEVEL': 'ERROR',
#     'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
# })

# process.crawl(OrganisatiesSpider)
# process.start()
