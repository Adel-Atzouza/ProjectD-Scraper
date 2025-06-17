import unittest
from scraper.visibility import is_visible  # hypothetisch pad


class TestJSVisibility(unittest.TestCase):
    def test_hidden_element(self):
        html = '<div style="display:none">Verborgen</div>'
        self.assertFalse(is_visible(html))

    def test_visible_element(self):
        html = "<div>Toon mij</div>"
        self.assertTrue(is_visible(html))
