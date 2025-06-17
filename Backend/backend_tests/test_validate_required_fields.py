
import unittest
from scraper.validation import validate_fields  # hypothetische module

class TestValidateRequiredFields(unittest.TestCase):
    def test_all_fields_present(self):
        row = {"naam": "Buurtcentrum", "type": "Activiteit", "email": "test@mail.nl"}
        self.assertTrue(validate_fields(row))

    def test_missing_fields(self):
        row = {"naam": "Buurtcentrum", "type": "", "email": ""}
        self.assertFalse(validate_fields(row))
