# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GoudaScraperItem(scrapy.Item):
    name = scrapy.Field()
    date = scrapy.Field()
    time = scrapy.Field()
    description = scrapy.Field()
    location = scrapy.Field()


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


class AlgemeneInfoItem(scrapy.Item):
    section = scrapy.Field()
    content = scrapy.Field()


class ActivityItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    date = scrapy.Field()
    time = scrapy.Field()
    location = scrapy.Field()
    contact_name = scrapy.Field()
    contact_email = scrapy.Field()
    contact_phone = scrapy.Field()
    url = scrapy.Field()
