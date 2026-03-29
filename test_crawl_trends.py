import unittest
from crawl_trends import is_ip_infringing, is_too_generic, generate_description

class TestCrawlTrends(unittest.TestCase):
    def test_is_ip_infringing(self):
        self.assertTrue(is_ip_infringing("mickey mouse t-shirt"))
        self.assertTrue(is_ip_infringing("marvel avengers merch"))
        self.assertTrue(is_ip_infringing("nba jersey shirt"))
        self.assertFalse(is_ip_infringing("autism wolf tshirt"))
        self.assertFalse(is_ip_infringing("funny quote tanktop"))

    def test_is_too_generic(self):
        self.assertTrue(is_too_generic("plain black tshirt"))
        self.assertTrue(is_too_generic("cheap white shirt"))
        self.assertTrue(is_too_generic("tshirt printing"))
        self.assertTrue(is_too_generic("tshirt")) # Too short
        self.assertFalse(is_too_generic("i love government tanktop"))
        self.assertFalse(is_too_generic("autism wolf tshirt"))

    def test_generate_description(self):
        desc = generate_description("autism wolf tshirt")
        self.assertIn("apparel search", desc.lower())
        self.assertIn("niche", desc.lower())

if __name__ == '__main__':
    unittest.main()
