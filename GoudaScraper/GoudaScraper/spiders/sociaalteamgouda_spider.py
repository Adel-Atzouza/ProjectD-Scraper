import scrapy
import re


class SociaalTeamSpider(scrapy.Spider):
    name = "sociaalteamgouda_spider"
    allowed_domains = ["sociaalteamgouda.nl"]
    start_urls = ["https://sociaalteamgouda.nl/ik-zoek-hulp/"]

    custom_settings = {
        "FEEDS": {"ik_zoek_hulp.csv": {"format": "csv", "overwrite": True}}
    }

    def parse(self, response):
        # Haal alle links naar de themapagina’s
        thema_links = response.css("div.entry-content a::attr(href)").getall()
        thema_links = [url for url in thema_links if "/thema/" in url]

        for link in thema_links:
            yield response.follow(link, callback=self.parse_thema)

    def parse_thema(self, response):
        thema = response.css("h1.entry-title::text").get(default="").strip()
        onderwerp_links = response.css(
            "div.entry-content a::attr(href)").getall()
        onderwerp_links = [
            url for url in onderwerp_links if "/onderwerp/" in url]

        for link in onderwerp_links:
            yield response.follow(
                link, callback=self.parse_onderwerp, meta={"thema": thema}
            )

    def parse_onderwerp(self, response):
        thema = response.meta["thema"]
        onderwerp = response.css(
            "h1.entry-title::text").get(default="").strip()

        # Alle tekstparagrafen ophalen
        content_paragraphs = response.css("div.entry-content p::text").getall()
        content_text = " ".join(p.strip()
                                for p in content_paragraphs if p.strip())

        # Ongewenste herhaling verwijderen
        content_text = re.sub(
            r"(Laat je telefoonnummer.*?088 900 4321\.)",
            "",
            content_text,
            flags=re.IGNORECASE,
        ).strip()

        # Externe links ophalen
        externe_links = response.css(
            "div.entry-content a::attr(href)").getall()
        externe_links = [
            url for url in externe_links if url.startswith("http")]

        yield {
            "Thema": thema,
            "Onderwerp": onderwerp,
            "Tekst": content_text,
            "Externe links": ", ".join(set(externe_links)),
            "URL": response.url,
        }
