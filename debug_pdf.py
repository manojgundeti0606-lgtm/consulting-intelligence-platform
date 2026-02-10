"""Debug PDF extraction"""
import requests
import io
from PyPDF2 import PdfReader

# Test downloading PDF
url = "https://goashipyard.in/assets/front/public/tender/GeM-Bidding-8311812.pdf"

session = requests.Session()
session.verify = False

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    response = session.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
    print(f"Content length: {len(response.content)} bytes")
    
    if response.status_code == 200 and len(response.content) > 1000:
        reader = PdfReader(io.BytesIO(response.content))
        print(f"Pages: {len(reader.pages)}")
        
        # Get metadata
        meta = reader.metadata
        if meta:
            print(f"Title: {meta.title}")
            print(f"Author: {meta.author}")
            print(f"Subject: {meta.subject}")
        
        # Get first page text
        if reader.pages:
            text = reader.pages[0].extract_text()
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            print(f"\nFirst few lines:")
            for line in lines[:10]:
                print(f"  {line[:80]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
