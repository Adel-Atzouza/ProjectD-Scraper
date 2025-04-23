import unittest
from scrapy.http import HtmlResponse, Request
from gouda_scraper.spiders.goudabruist import GoudaBruistSpider

class TestGoudaParsing(unittest.TestCase):

    def setUp(self):
        self.spider = GoudaBruistSpider()

    def test_parse_activities(self):
        html = '''
        <html>
          <body>
            <a href="/activiteit/123"><div class="card-body">
              <div class="go_day-name-wrapper">maandag</div>
              <div class="go_date-day-wrapper">10</div>
              <div class="go_date-month-wrapper">jun</div>
              <div class="go_date-time-wrapper">10:00</div>
              <div class="go_card-title-wrapper">Test Event</div>
              <div class="go_source-name-wrapper">Test Source</div>
              <div class="go_content-start-wrapper">Beschrijving</div>
            </div></a>
          </body>
        </html>
        '''
        request = Request(url='https://goudabruist.nl/activiteiten')
        response = HtmlResponse(url=request.url, body=html, encoding='utf-8', request=request)

        results = list(self.spider.parse_activities(response))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['Title'], 'Test Event')
        self.assertEqual(results[0]['Date'], '10 jun')
        self.assertEqual(results[0]['Time'], '10:00')
        self.assertEqual(results[0]['Source'], 'Test Source')
        self.assertEqual(results[0]['Description'], 'Beschrijving')
        self.assertEqual(results[0]['URL'], 'https://goudabruist.nl/activiteit/123')

if __name__ == '__main__':
    unittest.main()
