
import unittest
from scraper.utils import clean_html  # hypothetische functie

class TestCleanHTML(unittest.TestCase):
    def test_strip_tags(self):
        raw = "<div><strong>Hallo</strong> wereld&nbsp;</div>"
        cleaned = clean_html(raw)
        self.assertEqual(cleaned, "Hallo wereld")

    def test_nested_tags(self):
        raw = "<div><p><em>Test</em></p></div>"
        self.assertEqual(clean_html(raw), "Test")
