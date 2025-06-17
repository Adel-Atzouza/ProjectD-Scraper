<<<<<<< HEAD
from testscraper import UniversalSpider
=======
>>>>>>> dev
import sys
import os

# Voeg de map toe waar testscraper.py zit
sys.path.append(
    os.path.abspath(
        os.path.join(
<<<<<<< HEAD
            os.path.dirname(
                __file__), "../../TestScraper/universal_scraper/spiders"
        )
    )
)
=======
            os.path.dirname(__file__), "../../TestScraper/universal_scraper/spiders"
        )
    )
)
from testscraper import UniversalSpider
>>>>>>> dev


def test_is_internal_returns_true_for_same_domain():
    spider = UniversalSpider()
    spider.allowed_domains = ["example.com"]
    assert spider.is_internal("https://example.com/page") is True


def test_is_internal_returns_false_for_other_domain():
    spider = UniversalSpider()
    spider.allowed_domains = ["example.com"]
    assert spider.is_internal("https://external.com/page") is False
