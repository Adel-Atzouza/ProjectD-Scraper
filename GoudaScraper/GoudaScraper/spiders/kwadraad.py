import scrapy
import csv


class KwadraadKalenderSpider(scrapy.Spider):
    name = 'kwadraad_kalender'
    start_urls = ['https://www.kwadraad.nl/kalender/']
