# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class KwadraadItem(scrapy.Item):
    id = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    date = scrapy.Field()
    time = scrapy.Field()
    location = scrapy.Field()
    max_persons = scrapy.Field()
    contact_name = scrapy.Field()
    contact_phone = scrapy.Field()
    contact_email = scrapy.Field()
