import logging
import requests
from bs4 import BeautifulSoup
from portal_scrapers.nic_scraper import CPPPScraper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cppp_connection():
    print("Testing CPPP Connection...")
    scraper = CPPPScraper()
    url = scraper._get_page_url("FrontEndLatestActiveTenders")
    print(f"Target URL: {url}")
    
    try:
        response = scraper.session.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables")
            
            # Inspect first table rows
            if tables:
                rows = tables[0].find_all('tr')
                print(f"Table 0 has {len(rows)} rows")
                if len(rows) > 0:
                    print("First row text:", rows[0].get_text(strip=True)[:100])
                    
            # Try scraper logic
            print("\nRunning scrape_bids()...")
            bids = scraper.scrape_bids(max_pages=1)
            print(f"Scrape Result: {len(bids)} bids found")
            if bids:
                print(f"Sample Bid: {bids[0]}")
            else:
                print("No bids parsed. Check selectors.")
                
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    test_cppp_connection()
