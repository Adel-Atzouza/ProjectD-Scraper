import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_playwright.page import PageMethod
import re


class ContactenSpider(scrapy.Spider):
    name = "contacten_spider"
    start_urls = [
        "https://www.sportpuntgouda.nl/beweegmakelaars",
        "https://www.sportpuntgouda.nl/volwassenenfonds-sport-en-cultuur",
        "https://www.sportpuntgouda.nl/rotterdampas",
        "https://www.sportpuntgouda.nl/valpreventie",
        "https://www.sportpuntgouda.nl/gouda-goed-bezig-jogg",
        "https://www.sportpuntgouda.nl/inclusie",
        "https://www.sportpuntgouda.nl/sociaal-domein",
        "https://www.sportpuntgouda.nl/tipkaart-zorgverleners",
        "https://www.sportpuntgouda.nl/kenniscentrum"
    ]

    custom_settings = {
        "FEEDS": {
            "SportpunbGoudacontacten.csv": {
                "format": "csv",
                "fields": ["categorie", "naam", "functie", "telefoon", "email", "pagina_url"],
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
                meta={
                    "playwright": True,
                    "playwright_page_methods": [PageMethod("wait_for_timeout", 1000)]
                },
                callback=self.parse
            )

    def parse(self, response):
        url = response.url

        # Beweegmakelaars
        if "beweegmakelaars" in url:
            for card in response.css(".card-stretch-hover"):
                naam = card.css("h5.card-title::text").get(default="").strip()
                tekst = " ".join(card.xpath(".//p//text()").getall()).strip()
                telefoon = ""
                email = card.css("a[href^='mailto:']::attr(href)").get(default="").replace("mailto:", "").strip()
                matches = re.findall(r"(06\d{8})", tekst.replace(" ", "").replace("-", ""))
                if matches:
                    telefoon = matches[0]
                if naam and telefoon:
                    yield {
                        "categorie": "beweegmakelaars",
                        "naam": naam,
                        "functie": "",
                        "telefoon": telefoon,
                        "email": email,
                        "pagina_url": url
                    }

        # Volwassenenfonds
        elif "volwassenenfonds" in url:
            for li in response.css("ul > li"):
                tekst = " ".join(li.css("*::text").getall()).strip()
                naam = li.xpath(".//text()[1]").get(default="").strip()
                functie_match = re.search(r"(Beweegmakelaar.*?|Kennismetwerk.*?)\,", tekst)
                tel_match = re.search(r"(06[\s\d]{8,})", tekst)
                email = li.css("a[href^='mailto:']::attr(href)").get(default="").replace("mailto:", "").strip()

                if naam and tel_match:
                    yield {
                        "categorie": "volwassenenfonds",
                        "naam": naam,
                        "functie": functie_match.group(1) if functie_match else "",
                        "telefoon": tel_match.group(1).replace(" ", ""),
                        "email": email,
                        "pagina_url": url
                    }

        # Valpreventie
        elif "valpreventie" in url:
            naam = "Sabine"
            functie = "Valpreventie"
            telefoon = response.css('a[href^="tel:"]::text').get(default="").replace(" ", "")
            email = response.css('a[href^="mailto:"]::attr(href)').get(default="").replace("mailto:", "").strip()

            yield {
                "categorie": "valpreventie",
                "naam": naam,
                "functie": functie,
                "telefoon": telefoon,
                "email": email,
                "pagina_url": url
            }

        # Gezond eten (Gouda Goed Bezig JOGG)
        elif "gouda-goed-bezig-jogg" in url:
            naam = response.css("h6.card-title::text").get(default="").strip().split("|")[0].strip()
            functie = "Gouda Goed Bezig Regisseur"
            email = response.css("a[href^='mailto:']::attr(href)").get(default="").replace("mailto:", "").strip()
            yield {
                "categorie": "gezond eten",
                "naam": naam,
                "functie": functie,
                "telefoon": "",
                "email": email,
                "pagina_url": url
            }

        elif "kenniscentrum" in response.url:
            self.logger.info("📘 Kenniscentrum contactpersoon gevonden")

            titel = response.css("h5.card-title::text").get(default="").strip()
            if "|" in titel:
                naam, functie = [x.strip() for x in titel.split("|", 1)]
            else:
                naam, functie = titel, ""

            telefoon = response.css("a[href^='tel:']::attr(href)").get(default="").replace("tel:", "").strip()

            yield {
                "categorie": "kenniscentrum",
                "naam": naam,
                "functie": functie,
                "telefoon": telefoon,
                "email": "",  # niet aanwezig op deze pagina
                "pagina_url": response.url
            }


                # Inclusie
        elif "inclusie" in url:
            naam = "Kim"
            functie = "Coördinator Aangepast Sporten"
            email = response.css("a[href^='mailto:']::attr(href)").get(default="").replace("mailto:", "").strip()

            yield {
                "categorie": "inclusie",
                "naam": naam,
                "functie": functie,
                "telefoon": "",
                "email": email,
                "pagina_url": url
            }

        # Rotterdampas
        elif "rotterdampas" in url:
            yield {
                "categorie": "rotterdampas",
                "naam": "",
                "functie": "",
                "telefoon": "",
                "email": "",
                "pagina_url": url
            }

        elif "sociaal-domein" in url:
            for persoon in response.css("div.card-stretch-hover"):
                naam_functie = persoon.css("h6::text").get(default="").strip()
                email = persoon.css("a[href^='mailto:']::attr(href)").get(default="").replace("mailto:", "").strip()
                if naam_functie and email:
                    parts = naam_functie.split("|")
                    naam = parts[0].strip()
                    functie = parts[1].strip() if len(parts) > 1 else ""

                    yield {
                        "categorie": "sociaal domein",
                        "naam": naam,
                        "functie": functie,
                        "telefoon": "",
                        "email": email,
                        "pagina_url": url
                    }

        elif "tipkaart-zorgverleners" in response.url:
            self.logger.info("📄 Tipkaart Zorgverleners gevonden")

            titel = response.css("h5.card-title::text").get(default="").strip()
            if "|" in titel:
                naam, functie = [x.strip() for x in titel.split("|", 1)]
            else:
                naam, functie = titel, ""

            email = response.css("a[href^='mailto:']::attr(href)").get(default="").replace("mailto:", "").strip()

            yield {
                "categorie": "sport-zorgverleners",
                "naam": naam,
                "functie": functie,
                "telefoon": "",  # geen telefoon zichtbaar
                "email": email,
                "pagina_url": response.url
            }

        elif "gouds-leefstijlakkoord" in response.url:
            self.logger.info("💙 Gouds Leefstijlakkoord contactpersoon gevonden")

            titel = response.css("h5.card-title::text").get(default="").strip()
            if "|" in titel:
                naam, functie = [x.strip() for x in titel.split("|", 1)]
            else:
                naam, functie = titel, ""

            telefoon = response.css("a[href^='tel:']::attr(href)").get(default="").replace("tel:", "").strip()
            email = response.css("a[href^='mailto:']::attr(href)").get(default="").replace("mailto:", "").strip()

            yield {
                "categorie": "gouds leefstijlakkoord",
                "naam": naam,
                "functie": functie,
                "telefoon": telefoon,
                "email": email,
                "pagina_url": response.url
            }





# ✅ Start de spider
process = CrawlerProcess()
process.crawl(ContactenSpider)
process.start()
