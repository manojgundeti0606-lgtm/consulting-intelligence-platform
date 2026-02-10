"""Test script for DDP Selenium scraper"""
from portal_scrapers.ddp_selenium_scraper import scrape_ddp_selenium

print("Testing DDP Selenium scraper...")
bids = scrape_ddp_selenium()
print(f"Found {len(bids)} bids")
for bid in bids[:5]:
    title = bid.get('Items', 'NO TITLE')
    print(f"  - {title[:60]}")
