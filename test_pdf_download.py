"""Test downloading Goa Shipyard PDF with session from tender page"""
import requests
import io
from PyPDF2 import PdfReader
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create session and first visit tender page (to get cookies)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://goashipyard.in/tender/Tenders',
})
session.verify = False

# First visit tenders page to establish session
print("Visiting tender page first...")
resp = session.get('https://goashipyard.in/tender/Tenders', timeout=30)
print(f"Tender page status: {resp.status_code}")

# Now try downloading a PDF
pdf_url = "https://goashipyard.in/assets/front/public/tender/GeM-Bidding-8311812.pdf"
print(f"\nDownloading PDF: {pdf_url}")

try:
    pdf_resp = session.get(pdf_url, timeout=30)
    print(f"PDF response status: {pdf_resp.status_code}")
    print(f"Content-Type: {pdf_resp.headers.get('content-type', 'unknown')}")
    print(f"Content length: {len(pdf_resp.content)} bytes")
    
    # Check if it's actually a PDF
    if pdf_resp.content[:4] == b'%PDF':
        print("✅ Successfully downloaded PDF!")
        
        # Parse it
        reader = PdfReader(io.BytesIO(pdf_resp.content))
        print(f"Pages: {len(reader.pages)}")
        
        # Get first page text
        if reader.pages:
            text = reader.pages[0].extract_text()
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            print(f"\nFirst 15 lines of content:")
            for i, line in enumerate(lines[:15]):
                print(f"  {i+1}: {line[:80]}")
    else:
        print("❌ Response is not a PDF")
        print(f"First 200 chars: {pdf_resp.text[:200]}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
