"""
GeM-CPPP Scraper - Scrapes CPPP tenders via GeM's integrated endpoint.

This module provides a scraper for CPPP tenders using GeM's integration page
at https://gem.gov.in/cppp which:
- Does NOT require CAPTCHA (unlike direct CPPP access)
- Provides clean HTML table structure
- Has pagination support
- Contains 24,000+ active tenders
"""

import logging
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, ScrapedBid, PortalType

logger = logging.getLogger(__name__)


class GeMCPPPScraper(BaseScraper):
    """
    Scraper for CPPP tenders via GeM integration.
    
    Uses https://gem.gov.in/cppp which provides CPPP data without CAPTCHA.
    """
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://gem.gov.in/',
        'Connection': 'keep-alive',
    }
    
    BASE_URL = "https://gem.gov.in/cppp"
    
    def __init__(self):
        super().__init__(portal_type=PortalType.CPPP)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    @property
    def portal_name(self) -> str:
        return "CPPP (via GeM)"
    
    @property
    def base_url(self) -> str:
        return self.BASE_URL
    
    def _rate_limit(self, min_delay: float = 1.0, max_delay: float = 2.0):
        """Apply random delay between requests."""
        time.sleep(random.uniform(min_delay, max_delay))
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format."""
        if not date_str or date_str.strip() == 'N/A':
            return None
        
        # Clean the string
        date_str = date_str.strip()
        
        # Format: "23-February-2026 03:15:00 PM"
        date_formats = [
            "%d-%B-%Y %I:%M:%S %p",
            "%d-%B-%Y %H:%M:%S",
            "%d-%b-%Y %I:%M:%S %p",
            "%d-%b-%Y",
            "%d/%m/%Y %I:%M %p",
            "%d/%m/%Y",
        ]
        
        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _parse_tender_row(self, row) -> Optional[ScrapedBid]:
        """Parse a single tender row from the GeM-CPPP table."""
        cells = row.find_all('td')
        
        if len(cells) < 5:
            return None
        
        try:
            # Column structure:
            # 0: Bid Submission Closing Date
            # 1: Tender Opening Date  
            # 2: e-Published Date
            # 3: Title/Ref.No./Tender Id (with link)
            # 4: Organisation Name
            # 5: Corrigendum
            # 6: GeM Availability Report Id
            # 7: Download
            
            closing_date = cells[0].get_text(strip=True)
            opening_date = cells[1].get_text(strip=True)
            published_date = cells[2].get_text(strip=True)
            
            # Get title and tender ID from column 3
            title_cell = cells[3]
            title_link = title_cell.find('a')
            
            if title_link:
                full_text = title_link.get_text(strip=True)
                link = title_link.get('href', '')
            else:
                full_text = title_cell.get_text(strip=True)
                link = ''
            
            # Extract tender ID from the text (format: "Title/TenderId/Number")
            # The tender ID is usually after the last /
            parts = full_text.rsplit('/', 2)
            if len(parts) >= 2:
                title = parts[0].strip()
                tender_id = parts[-1].strip()
            else:
                title = full_text
                tender_id = ''
            
            # Get organization/department
            department = cells[4].get_text(strip=True) if len(cells) > 4 else ''
            
            # Generate a unique bid number
            bid_number = tender_id if tender_id else f"CPPP-{hash(full_text) % 100000000}"
            
            return ScrapedBid(
                bid_number=bid_number,
                title=title[:500],  # Truncate very long titles
                department=department,
                start_date=self._parse_date(published_date),
                end_date=self._parse_date(closing_date),
                document_link=link if link.startswith('http') else None,
                category="",  # Will be inferred
                estimated_value=None,  # Not available in this format
                location="India",  # Default for central tenders
                source_portal=PortalType.CPPP,
                raw_data={
                    'opening_date': opening_date,
                    'full_text': full_text,
                    'tender_id': tender_id,
                    'scrape_source': 'gem_cppp_integration'
                }
            )
            
        except Exception as e:
            logger.warning(f"Error parsing tender row: {e}")
            return None
    
    def _matches_keywords(self, bid: ScrapedBid, keywords: str) -> bool:
        """Check if bid matches any of the keywords."""
        if not keywords:
            return True
        
        keyword_list = [k.strip().lower() for k in keywords.split('|') if k.strip()]
        if not keyword_list:
            return True
        
        searchable = f"{bid.title} {bid.department}".lower()
        
        return any(kw in searchable for kw in keyword_list)
    
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
        Scrape CPPP bids from GeM integration page.
        
        Args:
            keywords: Pipe-separated keywords to filter results
            from_date: Not used (GeM CPPP shows active tenders only)
            to_date: Not used
            max_pages: Maximum pages to scrape (10 entries per page)
            categories: Not used
            
        Returns:
            List of ScrapedBid objects
        """
        all_bids = []
        
        logger.info(f"Starting GeM-CPPP scrape, max_pages={max_pages}")
        
        for page_num in range(1, max_pages + 1):
            try:
                # Build URL with pagination
                if page_num == 1:
                    url = self.BASE_URL
                else:
                    url = f"{self.BASE_URL}/{page_num}?"
                
                logger.info(f"Fetching page {page_num}: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the tender table
                table = soup.find('table', class_='table')
                if not table:
                    logger.warning(f"No table found on page {page_num}")
                    break
                
                tbody = table.find('tbody')
                if not tbody:
                    logger.warning(f"No tbody found on page {page_num}")
                    break
                
                rows = tbody.find_all('tr')
                logger.info(f"Found {len(rows)} rows on page {page_num}")
                
                page_bids = 0
                for row in rows:
                    bid = self._parse_tender_row(row)
                    if bid:
                        # Apply keyword filter
                        if self._matches_keywords(bid, keywords):
                            all_bids.append(bid)
                            page_bids += 1
                
                logger.info(f"Page {page_num}: extracted {page_bids} matching bids")
                
                # Rate limiting between pages
                if page_num < max_pages:
                    self._rate_limit()
                    
            except requests.RequestException as e:
                logger.error(f"Request error on page {page_num}: {e}")
                break
            except Exception as e:
                logger.error(f"Error parsing page {page_num}: {e}")
                continue
        
        logger.info(f"GeM-CPPP scrape complete: {len(all_bids)} total bids")
        return all_bids
    
    def get_bid_details(self, bid_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific bid."""
        # The GeM-CPPP page doesn't provide a detail view
        # Would need to follow the original CPPP/IREPS link
        return None


# For backward compatibility, also create CPPPScraper as an alias
class CPPPScraper(GeMCPPPScraper):
    """Alias for GeMCPPPScraper for backward compatibility."""
    pass


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing GeM-CPPP Scraper...")
    scraper = GeMCPPPScraper()
    
    # Test without keywords
    bids = scraper.scrape_bids(max_pages=2)
    print(f"Found {len(bids)} bids (no filter)")
    
    for bid in bids[:5]:
        print(f"  - {bid.bid_number}: {bid.title[:60]}...")
        print(f"    Dept: {bid.department[:40]}...")
        print(f"    End Date: {bid.end_date}")
        print()
    
    # Test with keywords
    print("\nTesting with consulting keywords...")
    bids = scraper.scrape_bids(keywords="consultant|advisory|PMU", max_pages=3)
    print(f"Found {len(bids)} matching bids")
    for bid in bids[:3]:
        print(f"  - {bid.title[:70]}...")
