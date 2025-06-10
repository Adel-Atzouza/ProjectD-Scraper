from pathlib import Path

import scrapy
import csv


class OnderwerpenSpider(scrapy.Spider):
    name = "ingouda_onderwerpen"

    def start_requests(self):
        urls = [
            "https://in-gouda.nl/onderwerpen/",
        ]

        self.data = []

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_onderwerpen)

    def parse_onderwerpen(self, response):
        onderwerp_artikels = response.css("li.subject-themes-grid-item")
        for artikel in onderwerp_artikels:
            onderwerp = artikel.css("a *::text").get()

            artikelen = artikel.css("li a::attr(href)").getall()[1:]

            artikelen_titles = artikel.css("li a::text").getall()

            if len(artikelen) < 2:
                continue

            assert len(artikelen) == len(
                artikelen_titles
            ), "Mismatch in number of artikelen and titles"

            for i, a in enumerate(artikelen):
                next_page = response.urljoin(a)
                yield scrapy.Request(
                    next_page,
                    callback=self.parse_artikel,
                    meta={"onderwerp": onderwerp, "subonderwerp": artikelen_titles[i]},
                )

    def parse_artikel(self, response):
        onderwerp = response.meta["onderwerp"]
        subonderwerp = response.meta["subonderwerp"]
        s = response.css("div.wp-block-sv-organisations-list")
        subsubonderwerptitles = s.css("a span::text").getall()
        subsubonderwerpen = s.css("a::attr(href)").getall()

        # artikel = " ".join(response.css("div.container *::text").getall()
        #                    ).replace("\n", " ").strip().replace('\r', ' ')

        assert len(subsubonderwerpen) == len(
            subsubonderwerptitles
        ), "Mismatch in number of subonderwerpen and titles"

        for i, a in enumerate(subsubonderwerpen):
            next_page = response.urljoin(a)
            yield scrapy.Request(
                next_page,
                callback=self.parse_artikel_artikel,
                meta={"o": [onderwerp, subonderwerp, subsubonderwerptitles[i], a]},
            )

    def parse_artikel_artikel(self, response):
        d = response.meta["o"]
        dd = response.css("main.entry-content *::text").getall()
        artikel = (
            " ".join(dd)
            .replace("  ", " ")
            .replace("  ", " ")
            .replace("  ", " ")
            .replace("  ", " ")
            .replace("  ", " ")
            .replace("\t", " ")
            .replace("\n", " ")
            .strip()
            .replace("\r", " ")
        )
        d += [artikel]
        self.data += [d]

    def save_in_csv(self, data):
        filename = "ingouda_onderwerpen.csv"
        file_path = Path(__file__).parent.parent / filename
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["onderwerp", "subonderwerp", "2ndsubonderwerp", "link", "description"]
            )
            data = sorted(data, key=lambda x: (x[0]))
            writer.writerows(data)
        print(f"Data saved to {file_path}")

    def close(self):
        self.save_in_csv(self.data)
        print("Spider closed. Data saved.")
