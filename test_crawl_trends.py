import unittest
from crawl_trends import is_ip_infringing, generate_idea

class TestCrawlTrends(unittest.TestCase):
    def test_is_ip_infringing(self):
        self.assertTrue(is_ip_infringing("disney shirt"))
        self.assertTrue(is_ip_infringing("marvel t-shirt"))
        self.assertTrue(is_ip_infringing("nike tank top"))
        self.assertTrue(is_ip_infringing("taylor swift merch"))
        self.assertTrue(is_ip_infringing("nba jersey"))
        self.assertFalse(is_ip_infringing("autism wolf tshirt"))
        self.assertFalse(is_ip_infringing("i love gardening shirt"))
        self.assertTrue(is_ip_infringing("hello kitty tee"))
        self.assertTrue(is_ip_infringing("star wars hoodie"))

    def test_generate_idea(self):
        self.assertEqual(generate_idea("autism wolf tshirt"), "Design featuring 'Autism Wolf'. Target audience interested in this trending topic.")
        self.assertEqual(generate_idea("i love gardening shirt"), "Design featuring 'I Love Gardening'. Target audience interested in this trending topic.")
        self.assertEqual(generate_idea("cool tanktop"), "Design featuring 'Cool'. Target audience interested in this trending topic.")

if __name__ == '__main__':
    unittest.main()
