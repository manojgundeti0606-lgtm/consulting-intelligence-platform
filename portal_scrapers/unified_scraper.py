"""
Unified Scraper - Multi-portal orchestration.

This module provides a unified interface to scrape from multiple
government tender portals simultaneously.

Author: Manoj Gundeti
"""

import logging
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .base_scraper import BaseScraper, ScrapedBid, PortalType, CONSULTING_CATEGORIES, DEFENCE_CATEGORIES
from .nic_scraper import CPPPScraper, DPPPScraper

logger = logging.getLogger(__name__)


class GeMScraperAdapter(BaseScraper):
    """
    Adapter for existing GeM scraper to work with unified interface.
    """
    
    def __init__(self):
        super().__init__(PortalType.GEM)
        self._gem_scraper = None
    
    @property
    def portal_name(self) -> str:
        return "Government e-Marketplace (GeM)"
    
    @property
    def base_url(self) -> str:
        return "https://bidplus.gem.gov.in"
    
    def _get_gem_scraper(self):
        """Lazy load the existing GeM scraper."""
        if self._gem_scraper is None:
            # Import the existing scraper
            import sys
            import os
            # Add parent directory to path
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from gem_scraper import scrape_bids
            self._scrape_bids_func = scrape_bids
        return self._scrape_bids_func
    
    def scrape_bids(
        self,
        keywords: str = "",
        from_date: str = "",
        to_date: str = "",
        max_pages: int = 5,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> List[ScrapedBid]:
        """Scrape bids from GeM using existing scraper."""
        try:
            scrape_func = self._get_gem_scraper()
            
            # Call existing GeM scraper
            consulting_only = kwargs.get('consulting_only', True)
            raw_bids = scrape_func(
                keywords=keywords,
                from_date=from_date,
                to_date=to_date,
                max_pages=max_pages,
                consulting_only=consulting_only
            )
            
            # Convert to ScrapedBid format
            scraped_bids = []
            for bid in raw_bids:
                scraped_bid = ScrapedBid(
                    bid_number=bid.get('Bid Number', ''),
                    title=bid.get('Items', ''),
                    department=bid.get('Department', ''),
                    start_date=bid.get('Start Date'),
                    end_date=bid.get('End Date'),
                    document_link=bid.get('Document Link'),
                    category=bid.get('Category'),
                    source_portal=PortalType.GEM,
                    raw_data=bid
                )
                scraped_bids.append(scraped_bid)
            
            # Apply category filter if provided
            if categories:
                scraped_bids = self.filter_by_category(scraped_bids, categories)
            
            return scraped_bids
            
        except Exception as e:
            self.logger.error(f"Error scraping GeM: {e}")
            return []
    
    def get_bid_details(self, bid_id: str) -> Optional[ScrapedBid]:
        """Get detailed information for a specific bid."""
        return None  # Delegate to existing implementation


class UnifiedScraper:
    """
    Unified scraper that orchestrates multiple portal scrapers.
    
    Usage:
        scraper = UnifiedScraper()
        bids = scraper.scrape_all_portals(keywords="consultancy")
        
        # Or scrape specific portals
        bids = scraper.scrape_portals(
            portals=[PortalType.GEM, PortalType.CPPP],
            keywords="IT services"
        )
    """
    
    def __init__(self):
        self.scrapers: Dict[PortalType, BaseScraper] = {
            PortalType.GEM: GeMScraperAdapter(),
            PortalType.CPPP: CPPPScraper(),
            PortalType.DPPP: DPPPScraper(),
        }
        self.logger = logging.getLogger(__name__)
    
    def get_available_portals(self) -> List[PortalType]:
        """Get list of available portal types."""
        return list(self.scrapers.keys())
    
    def get_portal_names(self) -> Dict[PortalType, str]:
        """Get portal type to name mapping."""
        return {pt: scraper.portal_name for pt, scraper in self.scrapers.items()}
    
    def scrape_portal(
        self,
        portal: PortalType,
        keywords: str = "",
        from_date: str = "",
        to_date: str = "",
        max_pages: int = 5,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> List[ScrapedBid]:
        """
        Scrape a single portal.
        
        Args:
            portal: Portal type to scrape
            keywords: Search keywords
            from_date: Start date filter
            to_date: End date filter
            max_pages: Maximum pages to scrape
            categories: Category filters
            
        Returns:
            List of scraped bids
        """
        if portal not in self.scrapers:
            self.logger.error(f"Unknown portal type: {portal}")
            return []
        
        scraper = self.scrapers[portal]
        return scraper.scrape_bids(
            keywords=keywords,
            from_date=from_date,
            to_date=to_date,
            max_pages=max_pages,
            categories=categories,
            **kwargs
        )
    
    def scrape_portals(
        self,
        portals: List[PortalType],
        keywords: str = "",
        from_date: str = "",
        to_date: str = "",
        max_pages: int = 5,
        categories: Optional[List[str]] = None,
        parallel: bool = True,
        **kwargs
    ) -> List[ScrapedBid]:
        """
        Scrape multiple portals.
        
        Args:
            portals: List of portal types to scrape
            keywords: Search keywords
            from_date: Start date filter
            to_date: End date filter
            max_pages: Maximum pages per portal
            categories: Category filters
            parallel: Run scrapers in parallel (default True)
            
        Returns:
            Combined list of scraped bids from all portals
        """
        all_bids = []
        
        if parallel and len(portals) > 1:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(
                        self.scrape_portal,
                        portal,
                        keywords,
                        from_date,
                        to_date,
                        max_pages,
                        categories,
                        **kwargs
                    ): portal
                    for portal in portals
                }
                
                for future in as_completed(futures):
                    portal = futures[future]
                    try:
                        bids = future.result()
                        all_bids.extend(bids)
                        self.logger.info(f"{portal.value}: {len(bids)} bids")
                    except Exception as e:
                        self.logger.error(f"Error scraping {portal.value}: {e}")
        else:
            # Sequential execution
            for portal in portals:
                try:
                    bids = self.scrape_portal(
                        portal,
                        keywords,
                        from_date,
                        to_date,
                        max_pages,
                        categories,
                        **kwargs
                    )
                    all_bids.extend(bids)
                    self.logger.info(f"{portal.value}: {len(bids)} bids")
                except Exception as e:
                    self.logger.error(f"Error scraping {portal.value}: {e}")
        
        return all_bids
    
    def scrape_all_portals(
        self,
        keywords: str = "",
        from_date: str = "",
        to_date: str = "",
        max_pages: int = 5,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> List[ScrapedBid]:
        """
        Scrape all available portals.
        
        Convenience method that scrapes GeM, CPPP, and DPPP.
        """
        return self.scrape_portals(
            portals=list(self.scrapers.keys()),
            keywords=keywords,
            from_date=from_date,
            to_date=to_date,
            max_pages=max_pages,
            categories=categories,
            **kwargs
        )
    
    def scrape_consulting_bids(
        self,
        portals: Optional[List[PortalType]] = None,
        max_pages: int = 5,
        **kwargs
    ) -> List[ScrapedBid]:
        """
        Scrape consulting-relevant bids from selected portals.
        
        Uses predefined consulting categories for filtering.
        """
        if portals is None:
            portals = list(self.scrapers.keys())
        
        return self.scrape_portals(
            portals=portals,
            categories=CONSULTING_CATEGORIES,
            max_pages=max_pages,
            **kwargs
        )
    
    def scrape_defence_bids(
        self,
        portals: Optional[List[PortalType]] = None,
        max_pages: int = 5,
        **kwargs
    ) -> List[ScrapedBid]:
        """
        Scrape defence-relevant bids from selected portals.
        
        Uses predefined defence categories for filtering.
        """
        if portals is None:
            portals = [PortalType.DPPP, PortalType.GEM]
        
        return self.scrape_portals(
            portals=portals,
            categories=DEFENCE_CATEGORIES,
            max_pages=max_pages,
            **kwargs
        )


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scraper = UnifiedScraper()
    
    print("Available portals:", scraper.get_portal_names())
    
    # Test scraping from CPPP only (faster for testing)
    print("\nScraping CPPP...")
    bids = scraper.scrape_portal(PortalType.CPPP, max_pages=1)
    print(f"Found {len(bids)} bids from CPPP")
    
    for bid in bids[:3]:
        print(f"  - [{bid.source_portal.value}] {bid.bid_number}: {bid.title[:40]}...")
