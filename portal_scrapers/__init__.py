"""
Multi-Portal Scraper Module

This module provides a unified interface for scraping government tender portals:
- GeM (Government e-Marketplace)
- CPPP (Central Public Procurement Portal)
- DPPP (Defence Procurement Portal)

Author: Manoj Gundeti
"""

from .base_scraper import BaseScraper, ScrapedBid, PortalType
from .nic_scraper import NICPortalScraper, CPPPScraper, DPPPScraper
from .unified_scraper import UnifiedScraper

__all__ = [
    'BaseScraper',
    'ScrapedBid',
    'PortalType',
    'NICPortalScraper',
    'CPPPScraper',
    'DPPPScraper',
    'UnifiedScraper',
]
