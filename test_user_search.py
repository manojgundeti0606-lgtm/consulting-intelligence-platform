from gem_scraper import scrape_bids
from datetime import datetime, timedelta

def test_user_search():
    keyword = "Ministry of Defence"
    
    # Last 3 months
    today = datetime.now()
    three_months_ago = today - timedelta(days=90)
    
    from_date = three_months_ago.strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    print(f"Testing search:")
    print(f"  Keyword: '{keyword}'")
    print(f"  From Date: {from_date}")
    print(f"  To Date: {to_date}")
    print()
    
    bids = scrape_bids(keywords=keyword, from_date=from_date, to_date=to_date, max_pages=2)
    
    if not bids:
        print("No bids found.")
        print("Testing without date filter...")
        bids_no_date = scrape_bids(keywords=keyword, max_pages=1)
        if bids_no_date:
            print(f"Found {len(bids_no_date)} bids WITHOUT date filter.")
            print("Sample bid dates:")
            for bid in bids_no_date[:3]:
                print(f"  {bid['Bid Number']}: End Date = {bid['End Date']}")
        return

    print(f"Found {len(bids)} bids with date filter.")
    for i, bid in enumerate(bids[:5]):
        print(f"{i+1}. {bid['Bid Number']} - {bid['Department'][:50]}")

if __name__ == "__main__":
    test_user_search()
