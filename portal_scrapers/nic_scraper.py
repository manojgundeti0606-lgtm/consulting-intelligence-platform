"""
NIC Portal Scraper - CPPP & DPPP Scraper Implementation.

This module provides scrapers for NIC-based eProcurement portals:
- CPPP (Central Public Procurement Portal) - eprocure.gov.in
- DPPP (Defence Procurement Portal) - defproc.gov.in

Both portals use the same NIC eProcurement framework, allowing
shared scraping logic.

Author: Manoj Gundeti
"""

import re
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlencode

from .base_scraper import BaseScraper, ScrapedBid, PortalType, CONSULTING_CATEGORIES

logger = logging.getLogger(__name__)


class NICPortalScraper(BaseScraper):
    """
    Scraper for NIC eProcurement portals (CPPP and DPPP).
    
    These portals share the same framework, so this class handles both
    with portal-specific URL configuration.
    """
    
    # Default request headers
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    def __init__(
        self, 
        portal_type: PortalType,
        base_url: str,
        app_path: str = "/app"
    ):
        super().__init__(portal_type)
        self._base_url = base_url
        self.app_path = app_path
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
    @property
    def portal_name(self) -> str:
        names = {
            PortalType.CPPP: "Central Public Procurement Portal (CPPP)",
            PortalType.DPPP: "Defence Procurement Portal (DPPP)",
            PortalType.EPROCURE: "eProcure Government of India",
            PortalType.GRSE: "Garden Reach Shipbuilders & Engineers (GRSE)",
        }
        return names.get(self.portal_type, "NIC eProcurement Portal")
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    def _get_page_url(self, page_name: str) -> str:
        """Build URL for a specific page."""
        return f"{self.base_url}{self.app_path}?page={page_name}&service=page"
    
    def _rate_limit(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Apply random delay between requests."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _parse_tender_row(self, row, cells) -> Optional[ScrapedBid]:
        """Parse a single tender row from the table."""
        try:
            # NIC portal table structure (Actual):
            # 0: S.No | 1: e-Published Date | 2: Bid Submission Closing Date | 3: Tender Opening Date | 4: Title and Ref | 5: Organisation Chain
            
            if len(cells) < 5:
                return None
            
            # Extract text from cells
            def get_text(cell):
                return cell.get_text(strip=True) if cell else ""
            
            # The title and ref are combined in cell 4
            title_ref_cell = cells[4]
            title_ref_text = get_text(title_ref_cell)
            
            # Try to find the tender link in cell 4
            tender_link = None
            for link in title_ref_cell.find_all('a', href=True):
                href = link.get('href', '')
                if 'DirectLink' in href or 'TenderDetails' in href:
                    tender_link = urljoin(self.base_url, href)
                    break
            
            # Split title and ref-no if possible
            # Usually format is "Title [Ref Num / Tender ID]"
            title = title_ref_text
            tender_ref = ""
            if '[' in title_ref_text and ']' in title_ref_text:
                parts = title_ref_text.split('[')
                title = parts[0].strip()
                tender_ref = parts[1].replace(']', '').strip()
            
            org_ministry = get_text(cells[5]) if len(cells) > 5 else ""
            closing_date = get_text(cells[2]) if len(cells) > 2 else ""
            
            if not tender_ref and not title:
                return None
            
            return ScrapedBid(
                bid_number=tender_ref or f"{self.portal_type.value.upper()}/{datetime.now().strftime('%Y%m%d')}/{hash(title) % 10000}",
                title=title,
                department=org_ministry,
                start_date=None,
                end_date=self._parse_date(closing_date),
                document_link=tender_link,
                category=None,
                location="",
                source_portal=self.portal_type,
                raw_data={
                    'cells': [get_text(c) for c in cells],
                    'tender_link': tender_link,
                }
            )
        except Exception as e:
            logger.warning(f"Error parsing tender row: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format."""
        if not date_str:
            return None
        
        # Common date formats in NIC portals
        formats = [
            '%d-%b-%Y %H:%M',
            '%d-%b-%Y',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
        
        return date_str  # Return as-is if parsing fails
    
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
        Scrape bids from NIC portal.
        
        Uses the Active Tenders page and optionally applies search filters.
        """
        all_bids = []
        
        try:
            # Start by fetching the active tenders page
            tenders_url = self._get_page_url("FrontEndLatestActiveTenders")
            
            self.logger.info(f"Scraping {self.portal_name}: {tenders_url}")
            
            for page in range(1, max_pages + 1):
                self._rate_limit()
                
                try:
                    response = self.session.get(tenders_url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find tender table - try multiple selectors
                    table = soup.find('table', id='table')
                    if not table:
                        table = soup.find('table', class_='list_table')
                    if not table:
                        # Try to find any table with tender data
                        tables = soup.find_all('table')
                        for t in tables:
                            if t.find('tr') and len(t.find_all('tr')) > 1:
                                # Check if this table has tender-like content
                                text = t.get_text().lower()
                                if 'tender' in text or 'closing' in text or 'organisation' in text:
                                    table = t
                                    break
                    
                    if table:
                        rows = table.find_all('tr')
                        header_found = False
                        
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            
                            # Skip header rows (contain 'S.No' or 'Organisation')
                            row_text = row.get_text().lower()
                            if 's.no' in row_text or 'organisation chain' in row_text:
                                header_found = True
                                continue
                            
                            # Only process rows after header with enough cells
                            if len(cells) >= 5:
                                bid = self._parse_tender_row(row, cells)
                                if bid:
                                    all_bids.append(bid)
                    else:
                        self.logger.warning(f"No tender table found on page {page}")
                    
                    # Check for next page link specifically by ID 'linkFwd'
                    next_link = soup.find('a', id='linkFwd')
                    if next_link and next_link.get('href'):
                        tenders_url = urljoin(self.base_url, next_link['href'])
                    else:
                        break  # No more pages
                    
                    self.logger.info(f"Page {page}: Found {len(all_bids)} bids so far")
                    
                except requests.RequestException as e:
                    self.logger.error(f"Error fetching page {page}: {e}")
                    break
            
            # Apply keyword filter only if keywords are provided and not empty
            if keywords:
                keywords_list = keywords if isinstance(keywords, list) else [keywords]
                keywords_lower = [k.lower().strip() for k in keywords_list if k and k.strip()]
                
                # Only filter if we have actual keywords (not just empty strings)
                if keywords_lower:
                    filtered_bids = []
                    for b in all_bids:
                        bid_text = f"{b.title} {b.department}".lower()
                        if any(k in bid_text for k in keywords_lower):
                            filtered_bids.append(b)
                    # Only apply filter if it doesn't eliminate all bids
                    if filtered_bids:
                        all_bids = filtered_bids
                    else:
                        self.logger.info(f"Keyword filter would eliminate all bids, keeping all {len(all_bids)}")
            
            # Apply category filter if requested
            if categories:
                all_bids = self.filter_by_category(all_bids, categories)
            
            self.logger.info(f"Total bids scraped from {self.portal_name}: {len(all_bids)}")
            
        except Exception as e:
            self.logger.error(f"Error scraping {self.portal_name}: {e}")
        
        return all_bids
    
    def get_bid_details(self, bid_id: str) -> Optional[ScrapedBid]:
        """Get detailed information for a specific bid."""
        # This would require navigating to the specific tender page
        # Implementation depends on how bid_id is structured
        self.logger.warning(f"get_bid_details not fully implemented for {self.portal_name}")
        return None


class CPPPScraper(NICPortalScraper):
    """
    Scraper for Central Public Procurement Portal (CPPP).
    
    URL: https://eprocure.gov.in
    """
    
    def __init__(self):
        super().__init__(
            portal_type=PortalType.CPPP,
            base_url="https://eprocure.gov.in/eprocure",
            app_path="/app"
        )


class DPPPScraper(NICPortalScraper):
    """
    Scraper for Defence Procurement Portal (DPPP).
    
    URL: https://defproc.gov.in
    """
    
    def __init__(self):
        super().__init__(
            portal_type=PortalType.DPPP,
            base_url="https://defproc.gov.in/nicgep",
            app_path="/app"
        )


class EProcureScraper(NICPortalScraper):
    """
    Scraper for eProcure Government Portal.
    
    URL: https://eprocure.gov.in/eprocure/app
    
    This portal uses the same NIC GEP framework as CPPP but with 
    different URL structure. It provides access to tenders from
    various central government organizations.
    """
    
    def __init__(self):
        super().__init__(
            portal_type=PortalType.EPROCURE,
            base_url="https://eprocure.gov.in/eprocure",
            app_path="/app"
        )


class GRSEScraper(NICPortalScraper):
    """
    Scraper for Garden Reach Shipbuilders & Engineers (GRSE) Portal.
    
    URL: https://eprocuregrse.co.in/nicgep/app
    
    This portal uses the NIC GEP framework specifically for GRSE tenders.
    It hosts tenders for shipbuilding and related defence contracts.
    """
    
    def __init__(self):
        super().__init__(
            portal_type=PortalType.GRSE,
            base_url="https://eprocuregrse.co.in/nicgep",
            app_path="/app"
        )


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test CPPP scraper
    print("Testing CPPP Scraper...")
    cppp = CPPPScraper()
    bids = cppp.scrape_bids(max_pages=1)
    print(f"CPPP: Found {len(bids)} bids")
    for bid in bids[:3]:
        print(f"  - {bid.bid_number}: {bid.title[:50]}...")
    
    print("\nTesting DPPP Scraper...")
    dppp = DPPPScraper()
    bids = dppp.scrape_bids(max_pages=1)
    print(f"DPPP: Found {len(bids)} bids")
    for bid in bids[:3]:
        print(f"  - {bid.bid_number}: {bid.title[:50]}...")
