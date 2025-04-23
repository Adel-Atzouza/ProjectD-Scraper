import scrapy

class GoudaScraperItem(scrapy.Item):
    name = scrapy.Field()
    date = scrapy.Field()
    time = scrapy.Field()
    description = scrapy.Field()
    location = scrapy.Field()
