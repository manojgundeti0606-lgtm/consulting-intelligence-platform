"""Test Goa Shipyard title extraction"""
from portal_scrapers.goa_shipyard_scraper import scrape_goa_shipyard

print("Goa Shipyard tenders with actual titles:\n")
bids = scrape_goa_shipyard()
print(f"Total: {len(bids)} bids\n")

# Show first 10
for i, bid in enumerate(bids[:10], 1):
    title = bid.get('Items', 'NO TITLE')
    bid_num = bid.get('Bid Number', '')
    print(f"{i}. [{bid_num}]")
    print(f"   {title}")
    print()
