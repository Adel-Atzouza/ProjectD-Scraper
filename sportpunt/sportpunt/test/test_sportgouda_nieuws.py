import unittest
from scrapy.http import HtmlResponse, Request
from sportpunt.spiders.sportgouda_nieuws import NieuwsSpider


class TestSportgoudaNieuwsSpider(unittest.TestCase):

    def setUp(self):
        self.spider = NieuwsSpider()

    def test_parse_single_news_item(self):
        html = '''
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Test Titel</h5>
                <i class="fa-calendar-alt"></i><span class="pl-2">1 januari 2025</span>
                <p class="card-text mt-2">Dit is een korte beschrijving.</p>
            </div>
            <a href="/nieuws/test-artikel" class="stretched-link"></a>
        </div>
        '''

        response = HtmlResponse(
            url='https://www.sportpuntgouda.nl/nieuws?page=1',
            body=html,
            encoding='utf-8'
        )

        results = list(self.spider.parse(response))
        self.assertEqual(len(results), 1)

        item = results[0]
        self.assertEqual(item['title'], 'Test Titel')
        self.assertEqual(item['date'], '1 januari 2025')
        self.assertEqual(item['description'], 'Dit is een korte beschrijving.')
        self.assertEqual(item['url'], 'https://www.sportpuntgouda.nl/nieuws/test-artikel')


if __name__ == '__main__':
    unittest.main()
