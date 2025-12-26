from gem_scraper import scrape_bids
import sys

def test_scraping():
    print("--- Testing Broad Search (Run Intelligence Now scenario) ---")
    try:
        # Simulate Run Intelligence Now (empty keywords)
        bids = scrape_bids(
            keywords="",
            from_date="",
            to_date="",
            max_pages=1, # Limit pages for quick test
            consulting_only=True
        )
        print(f"Broad search found {len(bids)} bids.")
    except Exception as e:
        print(f"ERROR in Broad Search: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Testing Keyword Search ---")
    try:
        # Simulate User Search
        bids = scrape_bids(
            keywords="Cloud",
            from_date="",
            to_date="",
            max_pages=1,
            consulting_only=True
        )
        print(f"Keyword search found {len(bids)} bids.")
    except Exception as e:
        print(f"ERROR in Keyword Search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraping()
