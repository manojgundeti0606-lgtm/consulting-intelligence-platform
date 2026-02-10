"""
Extract tender titles from Goa Shipyard page context.
Since PDFs cannot be downloaded directly, extract context from surrounding HTML elements.
"""
import requests
import re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_goa_shipyard_with_context():
    """Scrape Goa Shipyard and extract context around PDF links."""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    session.verify = False
    
    url = "https://goashipyard.in/tender/Tenders"
    response = session.get(url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("Looking for tender sections and context...")
    
    # Find all sections/categories
    sections = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div'], 
                              class_=re.compile(r'tender|title|heading|category', re.IGNORECASE))
    print(f"Found {len(sections)} titled sections")
    
    # Find PDF links with context
    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
    print(f"\nFound {len(pdf_links)} PDF links")
    
    tenders = []
    for link in pdf_links[:10]:
        href = link.get('href', '')
        filename = href.split('/')[-1]
        
        # Get link text
        link_text = link.get_text(strip=True)
        
        # Get parent context
        parent = link.find_parent(['li', 'tr', 'div', 'td', 'p'])
        parent_text = parent.get_text(strip=True) if parent else ""
        
        # Get previous sibling context
        prev_sibling = link.find_previous_sibling(['span', 'strong', 'b', 'p', 'div'])
        prev_text = prev_sibling.get_text(strip=True) if prev_sibling else ""
        
        # Get grandparent context (for table cells)
        grandparent = parent.find_parent(['tr', 'div', 'section']) if parent else None
        grandparent_text = grandparent.get_text(strip=True)[:200] if grandparent else ""
        
        # Check for GeM/NIT tender type
        is_gem = 'gem' in filename.lower() or 'gem' in href.lower()
        is_nit = 'nit' in filename.lower()
        
        tender_info = {
            'filename': filename,
            'link_text': link_text[:100] if link_text else "No text",
            'parent_text': parent_text[:150] if parent_text else "No parent",
            'prev_text': prev_text[:100] if prev_text else "No prev",
            'grandparent_text': grandparent_text,
            'is_gem': is_gem,
            'is_nit': is_nit,
        }
        tenders.append(tender_info)
        
        print(f"\n--- {filename} ---")
        print(f"  Link text: {link_text[:80] if link_text else 'None'}")
        print(f"  Parent: {parent_text[:80] if parent_text else 'None'}")
        print(f"  Type: {'GeM' if is_gem else 'NIT' if is_nit else 'Other'}")

if __name__ == "__main__":
    scrape_goa_shipyard_with_context()
