"""
Goa Shipyard Limited Tender Scraper

Scrapes tenders from https://goashipyard.in/tender/Tenders
This portal has a simple HTML structure with direct PDF links.

Author: Manoj Gundeti
"""

import logging
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional, Dict, Any

from .base_scraper import BaseScraper, ScrapedBid, PortalType

logger = logging.getLogger(__name__)


class GoaShipyardScraper(BaseScraper):
    """
    Scraper for Goa Shipyard Limited tenders.
    
    The website has a simple HTML structure with tender categories
    (Outsourcing, Civil, General Engineering, etc.) and direct PDF links.
    """
    
    BASE_URL = "https://goashipyard.in"
    TENDER_URL = "https://goashipyard.in/tender/Tenders"
    
    def __init__(self):
        super().__init__(PortalType.GOA_SHIPYARD)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        # Disable SSL verification for sites with certificate issues
        self.session.verify = False
        # Suppress SSL warning
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    @property
    def portal_name(self) -> str:
        return "Goa Shipyard Limited"
    
    @property
    def base_url(self) -> str:
        return self.BASE_URL
    
    def scrape_bids(
        self,
        keywords: str = "",
        from_date: str = "",
        to_date: str = "",
        max_pages: int = 5,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> List[ScrapedBid]:
        """
        Scrape all tenders from Goa Shipyard website.
        
        The site shows all active tenders on a single page with PDF links.
        """
        self.logger.info("Scraping Goa Shipyard tenders...")
        bids = []
        
        try:
            response = self.session.get(self.TENDER_URL, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all PDF links on the page
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
            
            # Filter for tender-related PDFs only
            tender_patterns = [
                r'gem[-_]?bidding',
                r'nit',
                r'tender',
                r'bid[-_]?doc',
                r'\d{7,}',  # Long number (likely bid ID)
            ]
            
            self.logger.info(f"Found {len(pdf_links)} PDF documents, filtering for tenders...")
            
            tender_links = []
            for link in pdf_links:
                href = link.get('href', '').lower()
                filename = href.split('/')[-1].lower()
                
                # Check if it matches tender patterns
                is_tender = any(re.search(pattern, filename) for pattern in tender_patterns)
                
                # Exclude known non-tender files
                exclude_patterns = ['certificate', 'handbook', 'policy', 'committee', 'audit', 'vpat', 'accessibility']
                is_excluded = any(excl in filename for excl in exclude_patterns)
                
                if is_tender and not is_excluded:
                    tender_links.append(link)
            
            self.logger.info(f"Filtered to {len(tender_links)} tender documents")
            
            for link in tender_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Make absolute URL if relative
                if href.startswith('/'):
                    href = f"{self.BASE_URL}{href}"
                elif not href.startswith('http'):
                    href = f"{self.BASE_URL}/{href}"
                
                # Extract tender info from filename and context
                filename = href.split('/')[-1]
                bid_number = self._extract_bid_number(filename)
                title = self._extract_title(link, filename)
                category = self._determine_category(link)
                
                # Note: For DPSU portals, we include all tenders since they're already defence-focused
                # Keyword filtering is skipped as it doesn't apply well to static tender lists
                
                bid = ScrapedBid(
                    bid_number=bid_number,
                    title=title,
                    department="Goa Shipyard Limited",
                    document_link=href,
                    category=category,
                    source_portal=PortalType.GOA_SHIPYARD,
                    raw_data={
                        'filename': filename,
                        'source_url': self.TENDER_URL,
                    }
                )
                bids.append(bid)
            
            self.logger.info(f"Scraped {len(bids)} tenders from Goa Shipyard")
            
        except requests.RequestException as e:
            self.logger.error(f"Error scraping Goa Shipyard: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        
        return bids
    
    def get_bid_details(self, bid_id: str) -> Optional[ScrapedBid]:
        """
        Get details for a specific bid.
        
        For Goa Shipyard, we search through the tender page to find the bid.
        """
        all_bids = self.scrape_bids()
        for bid in all_bids:
            if bid.bid_number == bid_id:
                return bid
        return None
    
    def _extract_bid_number(self, filename: str) -> str:
        """Extract bid number from PDF filename."""
        # Remove .pdf extension
        name = filename.replace('.pdf', '').replace('.PDF', '')
        
        # Look for GeM bid pattern
        gem_match = re.search(r'GeM[-_]?Bidding[-_]?(\d+)', name, re.IGNORECASE)
        if gem_match:
            return f"GSL/GeM/{gem_match.group(1)}"
        
        # Look for other patterns
        number_match = re.search(r'(\d{5,})', name)
        if number_match:
            return f"GSL/{number_match.group(1)}"
        
        # Use sanitized filename as ID
        sanitized = re.sub(r'[^\w\-]', '_', name)[:30]
        return f"GSL/{sanitized}"
    
    def _extract_title(self, link_element, filename: str) -> str:
        """Extract tender title from link context."""
        name = filename.replace('.pdf', '').replace('.PDF', '')
        
        # First, try parent elements for actual tender title
        # Parent text is like "BRC FOR HIRING SERVICES OF TOTAL STATION\n\n(PDF - 109KB)"
        parent = link_element.find_parent(['li', 'td', 'div', 'p', 'tr'])
        if parent:
            text = parent.get_text(strip=True)
            # Remove the PDF label like "(PDF - 109KB)"
            import re
            text = re.sub(r'\(PDF\s*-\s*\d+\s*KB\)', '', text, flags=re.IGNORECASE).strip()
            text = re.sub(r'\(\d+\s*KB\)', '', text).strip()  # Also remove just "(109KB)"
            
            # If we got a meaningful title (not just file size info)
            if text and len(text) > 10 and not text.startswith('('):
                # Prefix with GSL for Goa Shipyard Limited
                return f"GSL: {text[:150]}"
        
        # Fallback: Generate from filename for GeM bids
        gem_match = re.search(r'GeM[-_]?Bidding[-_]?(\d+)', name, re.IGNORECASE)
        if gem_match:
            bid_id = gem_match.group(1)
            return f"GSL GeM Tender {bid_id}"
        
        # Check for NIT pattern
        if 'nit' in name.lower():
            cleaned = re.sub(r'[-_]', ' ', name).replace('NIT', '').strip()
            return f"GSL NIT: {cleaned}"
        
        # Fall back to cleaned filename
        cleaned = re.sub(r'[-_]', ' ', name)
        return f"GSL Tender: {cleaned}" if cleaned else "GSL Tender"
    
    def _determine_category(self, link_element) -> str:
        """Determine tender category from page structure."""
        # Look for parent heading
        parent = link_element.find_parent(['div', 'section'])
        if parent:
            heading = parent.find_previous(['h2', 'h3', 'h4'])
            if heading:
                heading_text = heading.get_text(strip=True)
                if heading_text in ['Outsourcing', 'Civil', 'General Engineering Services']:
                    return heading_text
        
        # Check if in specific section
        for section in link_element.parents:
            section_id = section.get('id', '').lower()
            section_class = ' '.join(section.get('class', [])).lower()
            
            if 'outsourcing' in section_id or 'outsourcing' in section_class:
                return 'Outsourcing'
            elif 'civil' in section_id or 'civil' in section_class:
                return 'Civil'
            elif 'engineering' in section_id or 'engineering' in section_class:
                return 'General Engineering Services'
        
        return 'General'


# Convenience function
def scrape_goa_shipyard(keywords: str = "") -> List[Dict[str, Any]]:
    """Scrape Goa Shipyard tenders and return as list of dicts."""
    scraper = GoaShipyardScraper()
    bids = scraper.scrape_bids(keywords=keywords)
    return [bid.to_dict() for bid in bids]
