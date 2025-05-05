import scrapy
import csv
from pathlib import Path
from sociaalteamgouda.items import ActivityItem

class ActivitiesSpider(scrapy.Spider):
    name = "activities"
    allowed_domains = ["sociaalteamgouda.nl"]
    start_urls = ["https://sociaalteamgouda.nl/activiteiten/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        project_root = Path(__file__).resolve().parents[4]
        result_dir = project_root / "result"
        result_dir.mkdir(parents=True, exist_ok=True)

        self.output_file = (result_dir / "activities.csv").open("w", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.output_file)
        self.csv_writer.writerow([
            "title", "description", "date", "time", "location",
            "contact_name", "contact_email", "contact_phone", "url"
        ])

    def closed(self, reason):
        self.output_file.close()

    def parse(self, response):
        links = response.css('a.b-card::attr(href)').getall()
        for link in links:
            yield response.follow(link, callback=self.parse_activity)

    def parse_activity(self, response):
        title = response.css('h1.entry-title::text').get(default="").strip()

        # Clean and join only the paragraphs in the main content area
        description_parts = response.css('div.entry-content > p::text').getall()
        description = " ".join(p.strip() for p in description_parts if p.strip())
        description = description.replace("We konden geen gerelateerde activiteitsgebeurtenissen vinden.", "").strip()

        url = response.url

        # Extract optional details
        date = ""
        time = ""
        location = ""

        # Try to extract dates and times from description (primitive heuristic)
        import re
        date_match = re.search(r"\b\d{1,2} (januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december) \d{4}\b", description)
        if date_match:
            date = date_match.group(0)

        time_match = re.search(r"\b\d{1,2}[:.]\d{2}\s?(uur)?\b", description)
        if time_match:
            time = time_match.group(0)

        location_match = re.search(r"(?:in|bij|op)\s+(?:de\s)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?", description)
        if location_match:
            location = location_match.group(1)

        contact_name = response.css('.b-person__name::text').get(default="").strip()
        contact_email = response.css('a[href^="mailto:"]::text').get(default="").strip()
        contact_phone = response.css('a[href^="tel:"]::text').get(default="").strip()

        # Write to CSV
        self.csv_writer.writerow([
            title, description, date, time, location,
            contact_name, contact_email, contact_phone, url
        ])

        yield ActivityItem(
            title=title,
            description=description,
            date=date,
            time=time,
            location=location,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            url=url
        )
