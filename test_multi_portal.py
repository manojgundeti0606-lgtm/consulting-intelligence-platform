from portal_scrapers import UnifiedScraper
import logging

logging.basicConfig(level=logging.INFO)

print("Starting Unified Scraper Test...")
scraper = UnifiedScraper()
bids = scraper.scrape(
    portals=['gem', 'cppp', 'dppp'],
    keywords="Consultancy Services",
    max_pages=1,
    consulting_only=True
)

print(f"\nTotal bids found: {len(bids)}")
portals_found = {}
for bid in bids:
    portal = bid.get('Source Portal', 'unknown')
    portals_found[portal] = portals_found.get(portal, 0) + 1

print("Bids per portal:")
for portal, count in portals_found.items():
    print(f"  - {portal}: {count}")

if len(bids) > 0:
    print("\nSample Bids:")
    for bid in bids[:3]:
        print(f"  - [{bid.get('Source Portal')}] {bid.get('Bid Number')}: {bid.get('Items')[:50]}...")
