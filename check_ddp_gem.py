"""Check if DDP uploads bids on GeM"""
from gem_scraper import scrape_bids

# Search for DDP related bids on GeM
print("Searching GeM for DDP (Department of Defence Production) bids...")
bids = scrape_bids(keywords='Defence Production', max_pages=2)
print(f"Found {len(bids)} bids with 'Defence Production' keyword")

ddp_bids = []
for bid in bids:
    dept = bid.get('Department', '').lower()
    items = bid.get('Items', '').lower()
    if 'defence production' in dept or 'ddp' in dept or 'ddpmod' in dept:
        ddp_bids.append(bid)

print(f"\nBids from DDP specifically: {len(ddp_bids)}")
for bid in ddp_bids[:10]:
    print(f"  - {bid.get('Department', 'Unknown Department')}")
    print(f"    {bid.get('Items', 'No title')[:60]}")
    print()

# Also search with just 'DDP'
print("\n\nSearching with keyword 'DDP'...")
ddp_search = scrape_bids(keywords='DDP', max_pages=1)
print(f"Found {len(ddp_search)} bids")

for bid in ddp_search[:5]:
    print(f"  - {bid.get('Department', 'Unknown')[:50]} | {bid.get('Items', '')[:40]}")
