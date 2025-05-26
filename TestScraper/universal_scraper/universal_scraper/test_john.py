import pytest
from scrapy.http import HtmlResponse, Request
from scrapy_playwright.page import PageCoroutine
from unittest.mock import AsyncMock, patch
from spiders.universal import UniversalSpider  # Pas aan als je spider ergens anders staat


@pytest.fixture
def spider():
    return UniversalSpider()


def make_response(url, body_content, spider):
    request = Request(url=url, meta={'original_url': url})
    return HtmlResponse(url=url, body=body_content.encode(), encoding='utf-8', request=request)


def test_missing_body(spider):
    response = make_response("http://example.com", "<html><head></head></html>", spider)
    gen = spider.precheck(response)
    next_req = next(gen)
    assert next_req.meta['playwright'] is True
    assert isinstance(next_req.meta['playwright_page_coroutines'][0], PageCoroutine)


def test_present_body_no_js_needed(spider):
    response = make_response("http://example.com", "<body><p>Hello</p></body>", spider)
    gen = spider.precheck(response)
    next_req = next(gen)
    assert next_req.meta['playwright'] is False


@pytest.mark.asyncio
async def test_parse_handles_no_cookie_popup(spider):
    # Simuleer een Playwright-pagina zonder cookies
    page_mock = AsyncMock()
    page_mock.locator.return_value.count.return_value = 0
    page_mock.evaluate.return_value = 1000  # Scrollhoogte
    page_mock.content.return_value = "<body><p>Testtekst</p></body>"

    response = make_response("http://example.com", "<body></body>", spider)
    response.meta["playwright"] = True
    response.meta["playwright_page"] = page_mock

    result = [r async for r in spider.parse(response)]
    assert isinstance(result, list)
