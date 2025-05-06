import scrapy
from GoudaScraper.items import KwadraadItem
from fetcher import EVENT_LINKS

class KwadraadAgendaSpider(scrapy.Spider):
    name = "kwadraad_agenda"
    allowed_domains = ["zoekenboekgouda.kwadraad.nl"]

    def start_requests(self):
        for url in EVENT_LINKS:
            activity_id = self.extract_query_param(url, "activityPlanned")
            yield scrapy.Request(
                url=url,
                callback=self.parse_event_details,
                meta={'activity_id': activity_id}
            )

    def extract_query_param(self, url, param):
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(url).query)
        return query.get(param, [None])[0]

    def parse_event_details(self, response):
        def clean(selector):
            return selector.get(default="").strip().replace("\n", " ").replace("\r", "").strip()

        contact_blocks = response.css(".calendar-popup__contact-text > div")

        yield KwadraadItem(
            id=response.meta["activity_id"],
            title=clean(response.css(".calendar-popup__title::text")),
            subtitle=clean(response.css(".calendar-popup__description::text")),
            date=clean(response.css(".calendar-popup__date-text::text")),
            time=clean(response.css(".calendar-popup__time-text::text")),
            location=" ".join(response.css(".calendar-popup__location-text::text").getall()).strip(),
            max_persons=clean(response.css(".calendar-popup__max-amount::text")),
            contact_name=clean(contact_blocks[0].css("::text")) if len(contact_blocks) > 0 else None,
            contact_phone=" / ".join(contact_blocks[1].css("::text").getall()).strip() if len(contact_blocks) > 1 else None,
            contact_email=clean(contact_blocks[2].css("::text")) if len(contact_blocks) > 2 else None
        )
