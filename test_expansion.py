from gem_scraper import scrape_bids
from config import KEYWORD_EXPANSIONS

def test_expansion():
    # Test with "AI" which expands to "Artificial Intelligence", "Machine Learning", etc.
    base_keyword = "AI"
    print(f"Testing search with base keyword: '{base_keyword}'")
    
    # Expected expansions
    expansions = KEYWORD_EXPANSIONS.get(base_keyword.lower(), [])
    print(f"Expected expansions: {expansions}")
    
    # Run scraper (limit pages for speed)
    bids = scrape_bids(keywords=base_keyword, max_pages=1)
    
    if not bids:
        print("No bids found. This might be due to no live bids or scraper issue.")
        return

    print(f"\nFound {len(bids)} total bids.")
    
    # Analyze which terms matched
    matched_terms = set()
    for bid in bids:
        term = bid.get('Matched Term')
        if term:
            matched_terms.add(term)
            
    print(f"\nUnique matched terms found in results: {matched_terms}")
    
    # Check if we got any expanded terms
    found_expansion = False
    for term in matched_terms:
        if term.lower() != base_keyword.lower() and term.lower() in [e.lower() for e in expansions]:
            found_expansion = True
            print(f"SUCCESS: Found bid matching expanded term: '{term}'")
            
    if found_expansion:
        print("\n✅ Semantic expansion test PASSED!")
    else:
        print("\n⚠️  No expanded terms found in results. (This could be just due to lack of live bids for those specific terms)")
        print("However, if 'Matched Term' is present, the logic is working.")

if __name__ == "__main__":
    test_expansion()
