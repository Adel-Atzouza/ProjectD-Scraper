import unittest
from scraper.utils import extract_phone_number  # hypothetisch hulpfunctiepad


class TestPhoneNumberExtraction(unittest.TestCase):
    def test_valid_number(self):
        html = "<div>Contact: 06-12345678</div>"
        result = extract_phone_number(html)
        self.assertEqual(result, "06-12345678")

    def test_no_number(self):
        html = "<div>Geen telefoonnummer aanwezig</div>"
        result = extract_phone_number(html)
        self.assertIsNone(result)
