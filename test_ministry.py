from gem_scraper import scrape_bids

def test_ministry_search():
    keyword = "Ministry of Defence"
    print(f"Testing search with keyword: '{keyword}'")
    bids = scrape_bids(keywords=keyword, max_pages=1)
    
    if not bids:
        print("No bids found.")
        return

    print(f"Found {len(bids)} bids.")
    match_count = 0
    for bid in bids:
        dept = bid.get('Department', '')
        print(f"Bid: {bid['Bid Number']}, Dept: {dept}")
        if keyword.lower() in dept.lower():
            match_count += 1
            
    print(f"Matches found in Department field: {match_count}/{len(bids)}")

if __name__ == "__main__":
    test_ministry_search()
