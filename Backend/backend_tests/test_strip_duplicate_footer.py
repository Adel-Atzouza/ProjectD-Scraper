import unittest
from scraper.utils import is_footer_text  # hypothetische functie


class TestFooterDetection(unittest.TestCase):
    def test_detect_footer(self):
        text = "Over ons | Privacybeleid | Contact"
        self.assertTrue(is_footer_text(text))

    def test_non_footer(self):
        text = "Activiteit op maandag"
        self.assertFalse(is_footer_text(text))
