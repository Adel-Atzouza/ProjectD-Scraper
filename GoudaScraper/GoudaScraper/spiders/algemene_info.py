import scrapy
import csv
from pathlib import Path
from GoudaScraper.items import AlgemeneInfoItem


class AlgemeneInfoSpider(scrapy.Spider):
    name = "algemene_info"
    allowed_domains = ["sociaalteamgouda.nl"]
    start_urls = ["https://sociaalteamgouda.nl/wie-zijn-wij/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        project_root = Path(__file__).resolve().parents[4]
        result_dir = project_root / "result"
        result_dir.mkdir(parents=True, exist_ok=True)

        self.output_file = (
            result_dir /
            "algemene_info.csv").open(
            "w",
            newline="",
            encoding="utf-8")
        self.csv_writer = csv.writer(self.output_file)
        self.csv_writer.writerow(["section", "content"])

    def closed(self, reason):
        self.output_file.close()

    def parse(self, response):
        section = "Wie zijn wij"
        paragraphs = response.css("div.entry-content > p::text").getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        self.csv_writer.writerow([section, content])

        yield AlgemeneInfoItem(section=section, content=content)
