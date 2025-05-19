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
