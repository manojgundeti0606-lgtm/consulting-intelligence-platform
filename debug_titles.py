"""Debug script to check bid titles"""
from portal_scrapers.goa_shipyard_scraper import scrape_goa_shipyard
from portal_scrapers.ddp_scraper import scrape_ddp

print("Goa Shipyard bids:")
goa = scrape_goa_shipyard()[:5]
for b in goa:
    print(f"  Title: {b.get('Items', 'NO TITLE')}")
    print(f"  Bid#: {b.get('Bid Number')}")
    print(f"  Link: {b.get('Document Link', '')[:50]}...")
    print()

print("\nDDP bids:")
ddp = scrape_ddp()[:5]
for b in ddp:
    print(f"  Title: {b.get('Items', 'NO TITLE')}")
    print(f"  Bid#: {b.get('Bid Number')}")
    print()
