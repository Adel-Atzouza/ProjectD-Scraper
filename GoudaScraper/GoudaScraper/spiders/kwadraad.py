import scrapy
import csv


class KwadraadKalenderSpider(scrapy.Spider):
    name = 'kwadraad_kalender'
    start_urls = ['https://www.kwadraad.nl/kalender/']

    def __init__(self):
        self.csv_file = open('kwadraad_activiteiten.csv', mode='w', newline='', encoding='utf-8')
        fieldnames = ['Title', 'DateTime', 'Gemeente', 'Link']
        self.writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
        self.writer.writeheader()

    def parse(self, response):
        activities = response.css("article.archive-item")

        for item in activities:
            title = item.css("h2::text").get()
            date_time = item.css("span.date time::attr(datetime)").get()
            gemeente = item.css("span.date::text").re_first(r"→\s*(.+)")
            link = item.css("a.block-link::attr(href)").get()

            if title and date_time and gemeente and link:
                self.writer.writerow({
                    'Title': title.strip(),
                    'DateTime': date_time.strip(),
                    'Gemeente': gemeente.strip(),
                    'Link': link.strip()
                })

        next_page = response.css("span.prev a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def closed(self, reason):
        self.csv_file.close()
