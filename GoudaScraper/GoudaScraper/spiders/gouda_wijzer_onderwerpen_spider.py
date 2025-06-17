from pathlib import Path

import scrapy
import csv


class OnderwerpenSpider(scrapy.Spider):
    name = "onderwerpen"

    def start_requests(self):
        urls = [
            "https://www.goudawijzer.nl/is/een-vraag-over",
        ]

        self.data = []

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_onderwerpen)

    def parse_onderwerpen(self, response):
        onderwerpen = response.css(
            "a.articleMenuPanel__subjectAnchor::attr(href)"
        ).getall()
        onderwerp_titles = response.css(
            "a.articleMenuPanel__subjectAnchor span::text"
        ).getall()

        assert len(onderwerpen) == len(
            onderwerp_titles
        ), "Mismatch in number of onderwerpen and titles"
        assert len(onderwerpen) > 0, "No onderwerpen found"

        for i, onderwerp in enumerate(onderwerpen):

            next_page = response.urljoin(onderwerp)
            yield scrapy.Request(
                next_page,
                callback=self.parse_onderwerp_artikels,
                meta={"onderwerp": onderwerp_titles[i]},
            )

    def parse_onderwerp_artikels(self, response):
        onderwerp_artikels = response.css("div.indexSubjectItem")
        for artikel in onderwerp_artikels:
            subonderwerp = artikel.css(
                "h2.indexSubjectItem__header *::text").get()
            artikelen = artikel.css(
                "ul.indexSubjectSubItemContainer *::attr(href)"
            ).getall()

            assert len(subonderwerp) > 0, "No subonderwerp found"
            assert len(artikelen) > 0, "No artikelen found"

            for a in artikelen:
                next_page = response.urljoin(a)
                yield scrapy.Request(
                    next_page,
                    callback=self.parse_artikel,
                    meta={
                        "onderwerp": response.meta["onderwerp"],
                        "subonderwerp": subonderwerp,
                    },
                )

    def parse_artikel(self, response):
        onderwerp = response.meta["onderwerp"]
        subonderwerp = response.meta["subonderwerp"]
        artikel = (
            " ".join(response.css("div.container *::text").getall())
            .replace("\n", " ")
            .strip()
            .replace("\r", " ")
        )
        link = response.url

        assert len(onderwerp) > 0, "No onderwerp found"
        assert len(subonderwerp) > 0, "No subonderwerp found"
        assert link, "No link found"
        assert artikel, "No artikel found"

        self.data += [[onderwerp, subonderwerp, artikel, link]]

    def save_in_csv(self, data):
        filename = "onderwerpen.csv"
        file_path = Path(__file__).parent.parent / filename
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["onderwerp", "subonderwerp", "artikel", "link"])
            writer.writerows(data)
        print(f"Data saved to {file_path}")

    def close(self):
        self.save_in_csv(self.data)
        print("Spider closed. Data saved.")
