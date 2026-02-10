"""
Unified Scraper - Orchestrates scraping across multiple portals (GeM, CPPP, DPPP).
"""

import logging
import concurrent.futures
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from gem_scraper import scrape_bids as scrape_gem_bids
from .gem_cppp_scraper import GeMCPPPScraper  # Uses gem.gov.in/cppp (no CAPTCHA)
from .nic_scraper import DPPPScraper, EProcureScraper, GRSEScraper  # NIC GEP scrapers
from .goa_shipyard_scraper import GoaShipyardScraper  # Goa Shipyard
from .ddp_scraper import DDPScraper  # Dept of Defence Production
from .base_scraper import ScrapedBid, PortalType

logger = logging.getLogger(__name__)

class UnifiedScraper:
    """
    Coordinator for scraping multiple government tender portals.
    Unifies results into a common dictionary format compatible with the application.
    """
    
    def __init__(self):
        self.scrapers = {
            PortalType.CPPP.value: GeMCPPPScraper(),  # Uses gem.gov.in/cppp (no CAPTCHA!)
            PortalType.DPPP.value: DPPPScraper(),  # DPPP still has CAPTCHA issues
            # Phase 2 DPSU portals
            PortalType.EPROCURE.value: EProcureScraper(),
            PortalType.GRSE.value: GRSEScraper(),
            PortalType.GOA_SHIPYARD.value: GoaShipyardScraper(),
            PortalType.DDP.value: DDPScraper(),
        }
        # GeM is functional, so handled separately in scrape method
    
    def scrape(
        self,
        portals: List[str],
        keywords: Union[str, List[str]] = "",
        from_date: str = "",
        to_date: str = "",
        max_pages: int = None,
        consulting_only: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrape selected portals and return combined results.
        
        Args:
            portals: List of portal names ('gem', 'cppp', 'dppp')
            keywords: Search keywords
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            max_pages: Max pages per portal
            consulting_only: Whether to filter for consulting bids
            
        Returns:
            List of bid dictionaries
        """
        all_bids = []
        errors = []
        
        # Normalize portal names
        portals = [p.lower() for p in portals]
        
        # 1. Scrape GeM (if selected)
        if 'gem' in portals:
            try:
                logger.info("Starting GeM scraping...")
                gem_bids = scrape_gem_bids(
                    keywords=keywords,
                    from_date=from_date,
                    to_date=to_date,
                    max_pages=max_pages,
                    consulting_only=consulting_only,
                    **kwargs
                )
                
                # Enrich GeM bids with source portal if missing
                for bid in gem_bids:
                    if 'Source Portal' not in bid:
                        bid['Source Portal'] = 'gem'
                        
                all_bids.extend(gem_bids)
                logger.info(f"GeM scraping complete. Found {len(gem_bids)} bids.")
            except Exception as e:
                logger.error(f"Error scraping GeM: {e}")
                errors.append(f"GeM: {str(e)}")

        # 2. Scrape NIC Portals (CPPP, DPPP) and DPSU Portals (goa_shipyard, ddp, etc.)
        # These can be run in parallel
        nic_portals = [p for p in portals if p in self.scrapers]
        
        logger.info(f"Processing portals: {nic_portals} (from request: {portals})")
        print(f"DEBUG: Processing portals: {nic_portals} (requested: {portals})")
        
        if nic_portals:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(nic_portals)) as executor:
                future_to_portal = {
                    executor.submit(
                        self._scrape_nic_portal, 
                        portal_name, 
                        keywords, 
                        max_pages, 
                        consulting_only,
                        **kwargs
                    ): portal_name 
                    for portal_name in nic_portals
                }
                
                for future in concurrent.futures.as_completed(future_to_portal):
                    portal_name = future_to_portal[future]
                    try:
                        bids = future.result()
                        all_bids.extend(bids)
                        logger.info(f"{portal_name.upper()} scraping complete. Found {len(bids)} bids.")
                    except Exception as e:
                        logger.error(f"Error scraping {portal_name}: {e}")
                        errors.append(f"{portal_name}: {str(e)}")
        
        return all_bids

    def _scrape_nic_portal(
        self,
        portal_name: str,
        keywords: Union[str, List[str]],
        max_pages: int,
        consulting_only: bool,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Helper to run a specific NIC scraper and convert results."""
        scraper = self.scrapers.get(portal_name)
        if not scraper:
            return []
        
        # Convert keywords list to pipe-separated string if needed
        if isinstance(keywords, list):
            keywords_str = "|".join(keywords)
        else:
            keywords_str = keywords or ""
            
        # Default to 3 pages for NIC if not specified, as they can be slow
        pages = max_pages if max_pages else 3
        
        print(f"Starting {portal_name.upper()} scraping...")
        
        # Scrape
        scraped_objects = scraper.scrape_bids(
            keywords=keywords_str,
            max_pages=pages,
            **kwargs
        )
        
        # Filter (keywords matching is already done in nic_scraper, but double check consulting)
        # Note: nic_scraper.scrape_bids already handles keyword filtering
        
        # Convert to dicts
        results = [bid.to_dict() for bid in scraped_objects]
        return results

    def get_supported_portals(self) -> List[str]:
        """Return list of supported portal identifiers."""
        return ['gem'] + list(self.scrapers.keys())
