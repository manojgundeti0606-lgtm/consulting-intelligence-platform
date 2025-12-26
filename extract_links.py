"""
Extract all embedded links from bid PDF files
"""
import os
import re
import pdfplumber
from pathlib import Path

def extract_links_from_pdf(pdf_path):
    """Extract all URLs/links from a PDF file"""
    links = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text and find URLs using regex
                text = page.extract_text() or ""
                
                # URL patterns
                url_patterns = [
                    r'https?://[^\s<>"{}|\\^`\[\]]+',  # HTTP/HTTPS URLs
                    r'www\.[^\s<>"{}|\\^`\[\]]+',      # www links
                    r'ftp://[^\s<>"{}|\\^`\[\]]+',     # FTP links
                ]
                
                for pattern in url_patterns:
                    found_urls = re.findall(pattern, text)
                    for url in found_urls:
                        # Clean up URL (remove trailing punctuation)
                        url = url.rstrip('.,;:)')
                        links.append({
                            'url': url,
                            'page': page_num,
                            'source': 'text'
                        })
                
                # Also check for hyperlink annotations
                if hasattr(page, 'annots') and page.annots:
                    for annot in page.annots:
                        if annot.get('uri'):
                            links.append({
                                'url': annot['uri'],
                                'page': page_num,
                                'source': 'hyperlink'
                            })
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link['url'] not in seen:
            seen.add(link['url'])
            unique_links.append(link)
    
    return unique_links

def main():
    downloads_dir = Path("downloads")
    
    print("=" * 70)
    print("EXTRACTING LINKS FROM BID DOCUMENTS")
    print("=" * 70)
    
    all_links = {}
    
    # Process all PDF files
    pdf_files = list(downloads_dir.glob("*.pdf")) + list(downloads_dir.glob("**/*.pdf"))
    
    for pdf_file in sorted(pdf_files)[:20]:  # Limit to first 20 for quick scan
        bid_id = pdf_file.stem.strip("[]")
        print(f"\n📄 Processing: {pdf_file.name}")
        
        links = extract_links_from_pdf(pdf_file)
        
        if links:
            all_links[bid_id] = links
            print(f"   Found {len(links)} link(s):")
            for link in links:
                print(f"   - [Page {link['page']}] {link['url'][:80]}...")
        else:
            print("   No links found")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_links = sum(len(links) for links in all_links.values())
    print(f"Total PDFs scanned: {len(pdf_files[:20])}")
    print(f"PDFs with links: {len(all_links)}")
    print(f"Total unique links: {total_links}")
    
    return all_links

if __name__ == "__main__":
    main()
