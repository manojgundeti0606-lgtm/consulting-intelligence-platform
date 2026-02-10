from portal_scrapers import DPPPScraper, PortalType
import logging

logging.basicConfig(level=logging.INFO)

print("Starting DPPP Scraper Test...")
dppp = DPPPScraper()
# Scrape without keywords to see what's available
bids = dppp.scrape_bids(
    keywords="", 
    max_pages=3
)

print(f"\nTotal DPPP bids found: {len(bids)}")
if len(bids) > 0:
    print("\nSample DPPP Bids:")
    for bid in bids[:5]:
        b = bid.to_dict()
        print(f"  - {b['Bid Number']}: {b['Items'][:50]}... ({b['Department']})")
