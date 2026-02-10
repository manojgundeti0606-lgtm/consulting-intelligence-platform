"""Explore GeM-CPPP integration page"""
import requests
import json
import re
from bs4 import BeautifulSoup

session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
session.headers.update(headers)

# Get the GeM CPPP page
print("=== Analyzing GeM CPPP Page ===")
resp = session.get('https://gem.gov.in/cppp', timeout=30)
soup = BeautifulSoup(resp.text, 'html.parser')

# Find all tables
tables = soup.find_all('table')
print(f"Tables found: {len(tables)}")

for i, table in enumerate(tables):
    rows = table.find_all('tr')
    print(f"\nTable {i}: {len(rows)} rows")
    if rows:
        # Print headers
        headers_row = rows[0]
        cells = headers_row.find_all(['td', 'th'])
        headers_text = [c.get_text(strip=True)[:30] for c in cells]
        print(f"  Headers: {headers_text}")
        
        # Print first data row
        if len(rows) > 1:
            data_row = rows[1]
            cells = data_row.find_all(['td', 'th'])
            data_text = [c.get_text(strip=True)[:40] for c in cells]
            print(f"  Data: {data_text}")

# Look for JavaScript/AJAX calls
print("\n=== Looking for API endpoints ===")
scripts = soup.find_all('script')
for script in scripts:
    text = script.get_text()
    # Look for API URLs
    api_matches = re.findall(r'(https?://[^\s"\']+(?:api|data|ajax|fetch)[^\s"\']*)', text, re.IGNORECASE)
    if api_matches:
        print(f"API URLs found: {api_matches}")
    
    # Look for fetch/ajax calls
    if 'fetch(' in text or '$.ajax' in text or 'XMLHttpRequest' in text:
        # Extract URL patterns
        url_patterns = re.findall(r'["\']([^"\']+/[^"\']+)["\']', text)
        relevant = [u for u in url_patterns if 'cppp' in u.lower() or 'tender' in u.lower() or 'bid' in u.lower()]
        if relevant:
            print(f"Relevant URLs: {relevant[:5]}")

# Check for inline data
print("\n=== Looking for inline data ===")
page_text = resp.text

# Look for JSON data
json_patterns = re.findall(r'var\s+\w+\s*=\s*(\[{.+?}\]|\{.+?\});', page_text, re.DOTALL)
for pattern in json_patterns[:3]:
    if len(pattern) > 100 and len(pattern) < 5000:
        try:
            data = json.loads(pattern)
            print(f"JSON data found: {type(data)} with {len(data) if isinstance(data, list) else 'dict'} items")
        except:
            pass

# Look for any tender data in the page
print("\n=== Looking for tender data ===")
# Find divs with tender-like classes
tender_divs = soup.find_all(['div', 'section'], class_=lambda c: c and any(t in str(c).lower() for t in ['tender', 'bid', 'card']))
print(f"Tender-related divs: {len(tender_divs)}")

# Look for links to tender details
tender_links = soup.find_all('a', href=lambda h: h and ('tender' in h.lower() or 'bid' in h.lower() or 'cppp' in h.lower()))
print(f"Tender links: {len(tender_links)}")
for link in tender_links[:5]:
    print(f"  {link.get('href', '')[:80]}")

# Save page for inspection
with open('gem_cppp_page.html', 'w', encoding='utf-8') as f:
    f.write(resp.text)
print("\nPage saved to gem_cppp_page.html")
