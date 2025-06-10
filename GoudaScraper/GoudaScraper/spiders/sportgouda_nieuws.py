import scrapy


class NieuwsSpider(scrapy.Spider):
    name = "sportgouda_nieuws"
    allowed_domains = ["sportpuntgouda.nl"]
    start_urls = ["https://www.sportpuntgouda.nl/nieuws?page=1"]

    def parse(self, response):
        nieuwsblokken = response.css("div.card")
        self.logger.info(
            f"📦 Aantal nieuwsitems gevonden: {
                len(nieuwsblokken)}"
        )

        for blok in nieuwsblokken:
            try:
                title = blok.css("h5.card-title::text").get()
                date = blok.css("div.card-body i.fa-calendar-alt + span::text").get()
                description = blok.css("p.card-text::text").get()
                href = blok.css("a.stretched-link::attr(href)").get()

                if not all([title, date, description, href]):
                    self.logger.warning(
                        f"⚠️ Incomplete item gevonden (missende velden): {title}, {date}, {description}, {href}"
                    )

                full_url = response.urljoin(href) if href else None

                yield {
                    "title": title.strip() if title else None,
                    "date": date.strip() if date else None,
                    "description": description.strip() if description else None,
                    "url": full_url,
                }

            except Exception as e:
                self.logger.error(
                    f"❌ Fout bij het verwerken van item: {e}", exc_info=True
                )

        next_page = response.css("ul.pagination a.page-link::attr(href)").re_first(
            r"page=(\d+)"
        )
        if next_page:
            next_url = f"https://www.sportpuntgouda.nl/nieuws?page={next_page}"
            self.logger.info(f"➡️ Volgende pagina: {next_url}")
            yield scrapy.Request(url=next_url, callback=self.parse)
        else:
            self.logger.info("✅ Geen volgende pagina gevonden – scraping voltooid.")
