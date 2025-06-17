import unittest
from scraper.utils import normalize_url  # hypothetische normalisatie


class TestURLDeduplication(unittest.TestCase):
    def test_trailing_slash(self):
        url1 = "https://testsite.nl/contact"
        url2 = "https://testsite.nl/contact/"
        self.assertEqual(normalize_url(url1), normalize_url(url2))
