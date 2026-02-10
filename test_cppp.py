"""Test unified scraper with CPPP"""
import logging
logging.basicConfig(level=logging.INFO)

from portal_scrapers.unified_scraper import UnifiedScraper

print('Testing UnifiedScraper with CPPP...')
scraper = UnifiedScraper()
print(f'Supported portals: {scraper.get_supported_portals()}')

bids = scraper.scrape(portals=['cppp'], max_pages=2)
print(f'\nTotal CPPP bids: {len(bids)}')

for bid in bids[:3]:
    bid_num = bid.get('Bid Number', 'N/A')
    title = bid.get('Items', 'N/A')
    dept = bid.get('Department', 'N/A')
    source = bid.get('Source Portal', 'N/A')
    print(f"  - {bid_num}: {title[:50] if title else 'N/A'}...")
    print(f"    Dept: {dept[:40] if dept else 'N/A'}...")
    print(f"    Source: {source}")
