from portal_scrapers import UnifiedScraper
import sys
import logging
from datetime import datetime, timedelta
from config import KEYWORD_EXPANSIONS, DEFENCE_ORG_KEYWORDS

# Configuring logging to see scraper details
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_main():
    print(f"--- Starting Expanded Scraper Verification ---")
    scraper = UnifiedScraper()
    
    # Calculate dates
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Combine keywords (SIMULATING agent_scheduler.py)
    all_keywords = list(KEYWORD_EXPANSIONS.keys()) + DEFENCE_ORG_KEYWORDS
    unique_keywords = list(set(all_keywords))
    
    # Limit for debug speed (take first 5 + 'consultancy')
    debug_keywords = unique_keywords[:5]
    if 'consultancy' not in debug_keywords:
        debug_keywords.append('consultancy')
        
    print(f"Date Range: {yesterday} to {today} (Start Date Filter)")
    print(f"Total Configured Keywords: {len(unique_keywords)}")
    print(f"Testing with subset: {debug_keywords}")
    
    try:
        results = scraper.scrape(
            portals=['gem'],
            keywords=debug_keywords,
            from_date=yesterday,
            to_date=today,
            max_pages=2,
            consulting_only=True,
            date_filter_type='start'
        )
        
        print(f"\n✅ Found {len(results)} bids.")
        
        for i, b in enumerate(results[:5]):
            print(f"Bid {i+1}: {b.get('Bid Number')} - Start: {b.get('Start Date')} - Term: {b.get('Matched Term')}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_main()
