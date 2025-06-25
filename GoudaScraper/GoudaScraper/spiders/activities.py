import scrapy
import csv
from pathlib import Path
from GoudaScraper.items import ActivityItem


class ActivitiesSpider(scrapy.Spider):
    name = "activities"
    allowed_domains = ["sociaalteamgouda.nl"]
    start_urls = ["https://sociaalteamgouda.nl/activiteiten/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        project_root = Path(__file__).resolve().parents[4]
        result_dir = project_root / "result"
        result_dir.mkdir(parents=True, exist_ok=True)

        self.output_file = (result_dir / "activities.csv").open(
            "w", newline="", encoding="utf-8"
        )
        self.csv_writer = csv.writer(self.output_file)
        self.csv_writer.writerow(
            [
                "title",
                "date",
                "time",
                "location",
                "description",
                "contact_name",
                "contact_email",
                "contact_phone",
                "url",
            ]
        )

    def closed(self, reason):
        self.output_file.close()

    def parse(self, response):
        cards = response.css("a.b-card")
        for card in cards:
            url = card.css("::attr(href)").get()
            title = card.css("h3.b-card__title::text").get(default="").strip()
            date = card.css("span.start-date::text").get(default="").strip()
            time = card.css("span.start-date-time::text").get(default="").strip()
            time = " ".join(time.split())
            location = card.css("span.text::text").get(default="").strip()

            # Pass extracted data to the detail page
            yield response.follow(
                url,
                callback=self.parse_detail,
                meta={
                    "title": title,
                    "date": date,
                    "time": time,
                    "location": location,
                    "url": response.urljoin(url),
                },
            )

    def parse_detail(self, response):
        title = response.meta["title"]
        date = response.meta["date"]
        time = response.meta["time"]
        location = response.meta["location"]
        url = response.meta["url"]

        # Clean and focused description
        content_blocks = response.css("div.entry-content > *")
        paragraphs = []
        for block in content_blocks:
            # Ignore forms, scripts, and interactive divs
            if block.root.tag in ["script", "form"]:
                continue
            text = block.xpath("string(.)").get(default="").strip()
            if (
                text
                and "E-mailadres (Vereist)" not in text
                and "document.getElementById" not in text
            ):
                paragraphs.append(text)

        description = " ".join(paragraphs).strip()

        # Contact details
        contact_name = response.css(".b-person__name::text").get(default="").strip()
        contact_email = response.css('a[href^="mailto:"]::text').get(default="").strip()
        contact_phone = response.css('a[href^="tel:"]::text').get(default="").strip()

        self.csv_writer.writerow(
            [
                title,
                date,
                time,
                location,
                description,
                contact_name,
                contact_email,
                contact_phone,
                url,
            ]
        )

        yield ActivityItem(
            title=title,
            date=date,
            time=time,
            location=location,
            description=description,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            url=url,
        )
