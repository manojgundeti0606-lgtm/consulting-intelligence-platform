"""Analyze DDP page HTML in detail"""
import requests
from bs4 import BeautifulSoup

url = "https://www.ddpmod.gov.in/offerings/tenders-of-ddp"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
r = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(r.text, "html.parser")

print(f"Page title: {soup.title.string if soup.title else 'No title'}")
print(f"Content length: {len(r.text)} chars")

# Look for any elements with "tender" in class or id
tender_elements = soup.find_all(class_=lambda x: x and 'tender' in str(x).lower())
print(f"\nElements with 'tender' class: {len(tender_elements)}")

# Look for download/document links
doc_links = soup.find_all('a', href=lambda x: x and ('download' in str(x).lower() or 'document' in str(x).lower() or 'pdf' in str(x).lower()))
print(f"Document links: {len(doc_links)}")
for link in doc_links[:5]:
    print(f"  {link.get('href')}")

# Look for the main content area
article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
if article:
    all_links = article.find_all('a', href=True)
    print(f"\nLinks in main content: {len(all_links)}")
    for link in all_links[:10]:
        href = link.get('href', '')
        text = link.get_text(strip=True)[:50]
        print(f"  '{text}' -> {href[:50]}")

# Print all headings to understand structure
headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
print(f"\nHeadings: {len(headings)}")
for h in headings[:10]:
    print(f"  {h.name}: {h.get_text(strip=True)[:60]}")

# Save raw HTML for inspection
with open("ddp_page.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print("\nSaved full HTML to ddp_page.html")
