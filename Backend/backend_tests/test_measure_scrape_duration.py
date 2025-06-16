
import unittest
import time

class TestScrapeDuration(unittest.TestCase):
    def test_scrape_timing(self):
        start = time.time()
        time.sleep(0.1)
        end = time.time()
        duration = end - start
        self.assertGreater(duration, 0)
        self.assertLess(duration, 1)
