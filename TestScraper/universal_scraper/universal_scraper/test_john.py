import pytest
from scrapy.http import HtmlResponse, Request
from unittest.mock import MagicMock
from universal_scraper.spiders.testscraper import UniversalSpider


def test_missing_body():
    spider = UniversalSpider()
    url = "http://example.com/test"
    request = Request(url=url, meta={'original_url': url})

    html = "<html><head><title>No body</title></head></html>"
    response = HtmlResponse(url=url, request=request, body=html, encoding='utf-8')

    result = list(spider.precheck(response))
    assert len(result) == 1
    req = result[0]
    assert req.meta['playwright'] is True
