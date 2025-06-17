import scrapy


class ContactSpider(scrapy.Spider):
    name = "contact_spider"
    start_urls = ["https://sociaalteamgouda.nl/contact/"]

    custom_settings = {"FEEDS": {"contact.csv": {
        "format": "csv", "overwrite": True}}}

    def parse(self, response):
        page_text = response.css("main *::text").getall()
        cleaned_text = [t.strip() for t in page_text if t.strip()]

        yield {"url": response.url, "tekst": "\n".join(cleaned_text)}
