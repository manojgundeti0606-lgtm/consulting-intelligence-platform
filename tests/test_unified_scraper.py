import unittest
from unittest.mock import MagicMock, patch
from portal_scrapers import UnifiedScraper, PortalType, ScrapedBid

class TestUnifiedScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = UnifiedScraper()

    @patch('portal_scrapers.unified_scraper.scrape_gem_bids')
    @patch('portal_scrapers.nic_scraper.CPPPScraper.scrape_bids')
    def test_scrape_multi_portal(self, mock_cppp, mock_gem):
        # Mock GeM results (returns dicts)
        mock_gem.return_value = [
            {'Bid Number': 'GEM/1', 'Source Portal': 'gem', 'Items': 'Test Item 1'}
        ]
        
        # Mock CPPP results (returns ScrapedBid objects)
        mock_cppp.return_value = [
            ScrapedBid(
                bid_number='CPPP/1',
                title='Test Tender 1',
                department='Ministry of Testing',
                source_portal=PortalType.CPPP
            )
        ]
        
        # Run scraper
        results = self.scraper.scrape(
            portals=['gem', 'cppp'],
            keywords="test"
        )
        
        # Verify aggregation
        self.assertEqual(len(results), 2)
        
        # Verify GeM result
        self.assertEqual(results[0]['Bid Number'], 'GEM/1')
        self.assertEqual(results[0]['Source Portal'], 'gem')
        
        # Verify CPPP result (should be converted to dict)
        self.assertEqual(results[1]['Bid Number'], 'CPPP/1')
        self.assertEqual(results[1]['Items'], 'Test Tender 1')
        self.assertEqual(results[1]['Source Portal'], 'cppp')

if __name__ == '__main__':
    unittest.main()
