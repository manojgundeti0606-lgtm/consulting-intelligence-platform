"""
Department of Defence Production (DDP) Tender Scraper

Scrapes tenders from https://www.ddpmod.gov.in/offerings/tenders-of-ddp
This portal has a simple HTML structure with tender listings.

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


class DDPScraper(BaseScraper):
    """
    Scraper for Department of Defence Production tenders.
    
    The website has tender listings with links to PDF documents.
    """
    
    BASE_URL = "https://www.ddpmod.gov.in"
    TENDER_URL = "https://www.ddpmod.gov.in/offerings/tenders-of-ddp"
    ARCHIVE_URL = "https://www.ddpmod.gov.in/offerings/tenders-of-ddp/archive-page"
    
    def __init__(self):
        super().__init__(PortalType.DDP)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
    
    @property
    def portal_name(self) -> str:
        return "Department of Defence Production"
    
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
        include_archive: bool = False,
        **kwargs
    ) -> List[ScrapedBid]:
        """
        Scrape all tenders from DDP website.
        
        Args:
            include_archive: If True, also scrape archived tenders
        """
        self.logger.info("Scraping DDP tenders...")
        bids = []
        
        # Scrape main tenders page
        main_bids = self._scrape_page(self.TENDER_URL)
        bids.extend(main_bids)
        
        # Optionally scrape archive
        if include_archive:
            archive_bids = self._scrape_page(self.ARCHIVE_URL)
            bids.extend(archive_bids)
        
        # Note: For DPSU portals, we include all tenders since they're already defence-focused
        # Keyword filtering is skipped as it doesn't apply well to static tender lists
        
        self.logger.info(f"Scraped {len(bids)} tenders from DDP")
        return bids
    
    def _scrape_page(self, url: str) -> List[ScrapedBid]:
        """Scrape a single DDP page for tenders."""
        bids = []
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find tender links - typically PDF or document links
            # DDP site may have various structures, try multiple selectors
            
            # Method 1: Look for PDF links
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
            for link in pdf_links:
                bid = self._parse_tender_link(link)
                if bid:
                    bids.append(bid)
            
            # Method 2: Look for tender listings in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    bid = self._parse_table_row(row)
                    if bid:
                        bids.append(bid)
            
            # Method 3: Look for tender cards/listings
            listings = soup.find_all(['div', 'li'], class_=re.compile(r'tender|listing|item', re.IGNORECASE))
            for listing in listings:
                bid = self._parse_listing(listing)
                if bid:
                    bids.append(bid)
            
        except requests.RequestException as e:
            self.logger.error(f"Error scraping {url}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {url}: {e}")
        
        return bids
    
    def _parse_tender_link(self, link) -> Optional[ScrapedBid]:
        """Parse a tender PDF link."""
        href = link.get('href', '')
        if not href:
            return None
        
        # Skip navigation links and non-tender content
        nav_patterns = ['about', 'contact', 'home', 'team', 'policy', 'act', 'annual-report',
                        'press', 'notice', 'publication', 'useful-link', 'accessibility',
                        '#', 'javascript:', 'mailto:']
        href_lower = href.lower()
        if any(pattern in href_lower for pattern in nav_patterns):
            return None
        
        # Only include PDFs or document downloads
        if not href.endswith('.pdf') and '/download' not in href_lower:
            return None
        
        # Make absolute URL
        if href.startswith('/'):
            href = f"{self.BASE_URL}{href}"
        elif not href.startswith('http'):
            href = f"{self.BASE_URL}/{href}"
        
        filename = href.split('/')[-1]
        title = link.get_text(strip=True) or filename.replace('.pdf', '')
        
        # Skip if title is too short or generic
        if len(title) < 5 or title.lower() in ['download', 'click here', 'pdf', 'link']:
            return None
        
        # Look for context from parent elements
        parent = link.find_parent(['li', 'td', 'div', 'p'])
        if parent:
            parent_text = parent.get_text(strip=True)
            if len(parent_text) > len(title) and len(parent_text) < 300:
                title = parent_text
        
        # Add DDP prefix if not present
        if not title.lower().startswith('ddp') and not title.lower().startswith('defence'):
            title = f"DDP: {title}"
        
        # Extract date if present
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', title)
        end_date = date_match.group(1) if date_match else None
        
        bid_number = self._generate_bid_number(filename)
        
        return ScrapedBid(
            bid_number=bid_number,
            title=title[:200],  # Limit title length
            department="Department of Defence Production",
            document_link=href,
            end_date=end_date,
            category="Defence",
            source_portal=PortalType.DDP,
            raw_data={
                'filename': filename,
                'source_url': self.TENDER_URL,
            }
        )
    
    def _parse_table_row(self, row) -> Optional[ScrapedBid]:
        """Parse a table row for tender info."""
        cells = row.find_all('td')
        if len(cells) < 2:
            return None
        
        # Try to find document link
        link = row.find('a', href=True)
        if not link:
            return None
        
        href = link.get('href', '')
        if href.startswith('/'):
            href = f"{self.BASE_URL}{href}"
        
        # Extract info from cells
        title = cells[0].get_text(strip=True) if cells else "DDP Tender"
        end_date = None
        
        # Look for date in cells
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', cell_text)
            if date_match:
                end_date = date_match.group(1)
                break
        
        bid_number = self._generate_bid_number(href.split('/')[-1] if href else title)
        
        return ScrapedBid(
            bid_number=bid_number,
            title=title[:200],
            department="Department of Defence Production",
            document_link=href,
            end_date=end_date,
            category="Defence",
            source_portal=PortalType.DDP,
            raw_data={'source_url': self.TENDER_URL}
        )
    
    def _parse_listing(self, listing) -> Optional[ScrapedBid]:
        """Parse a tender listing element."""
        link = listing.find('a', href=True)
        if not link:
            return None
        
        return self._parse_tender_link(link)
    
    def _generate_bid_number(self, identifier: str) -> str:
        """Generate a unique bid number from identifier."""
        # Clean up identifier
        clean = re.sub(r'[^\w\-]', '_', identifier)[:30]
        
        # Look for existing number pattern
        num_match = re.search(r'(\d{5,})', identifier)
        if num_match:
            return f"DDP/{num_match.group(1)}"
        
        return f"DDP/{clean}"
    
    def get_bid_details(self, bid_id: str) -> Optional[ScrapedBid]:
        """Get details for a specific bid."""
        all_bids = self.scrape_bids(include_archive=True)
        for bid in all_bids:
            if bid.bid_number == bid_id:
                return bid
        return None


# Convenience function
def scrape_ddp(keywords: str = "", include_archive: bool = False) -> List[Dict[str, Any]]:
    """Scrape DDP tenders and return as list of dicts."""
    scraper = DDPScraper()
    bids = scraper.scrape_bids(keywords=keywords, include_archive=include_archive)
    return [bid.to_dict() for bid in bids]
