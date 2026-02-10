"""
Base Scraper - Abstract interface for all portal scrapers.

This module defines the common interface and data structures
for government tender portal scrapers.

Author: Manoj Gundeti
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


logger = logging.getLogger(__name__)


class PortalType(Enum):
    """Supported tender portal types."""
    GEM = "gem"
    CPPP = "cppp"
    DPPP = "dppp"
    # Phase 2 DPSU Portals
    EPROCURE = "eprocure"
    GRSE = "grse"
    GOA_SHIPYARD = "goa_shipyard"
    DDP = "ddp"
    BDL = "bdl"
    HAL = "hal"
    BHEL = "bhel"


@dataclass
class ScrapedBid:
    """
    Normalized bid data from any portal.
    
    All scrapers must convert their portal-specific data to this format.
    """
    bid_number: str
    title: str
    department: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    document_link: Optional[str] = None
    category: Optional[str] = None
    emd_amount: Optional[str] = None
    estimated_value: Optional[str] = None
    location: Optional[str] = None
    source_portal: PortalType = PortalType.GEM
    raw_data: Dict[str, Any] = field(default_factory=dict)
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format compatible with existing database."""
        return {
            'Bid Number': self.bid_number,
            'Items': self.title,
            'Department': self.department,
            'Start Date': self.start_date,
            'End Date': self.end_date,
            'Document Link': self.document_link,
            'Category': self.category,
            'EMD': self.emd_amount,
            'Estimated Value': self.estimated_value,
            'Location': self.location,
            'Source Portal': self.source_portal.value,
            'Scraped At': self.scraped_at,
        }


class BaseScraper(ABC):
    """
    Abstract base class for portal scrapers.
    
    All portal-specific scrapers must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, portal_type: PortalType):
        self.portal_type = portal_type
        self.logger = logging.getLogger(f"{__name__}.{portal_type.value}")
    
    @property
    @abstractmethod
    def portal_name(self) -> str:
        """Human-readable portal name."""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL of the portal."""
        pass
    
    @abstractmethod
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
        Scrape bids from the portal.
        
        Args:
            keywords: Search keywords
            from_date: Start date filter (YYYY-MM-DD)
            to_date: End date filter (YYYY-MM-DD)
            max_pages: Maximum pages to scrape
            categories: Category filters (consulting, IT, defence, etc.)
            **kwargs: Portal-specific arguments
            
        Returns:
            List of normalized ScrapedBid objects
        """
        pass
    
    @abstractmethod
    def get_bid_details(self, bid_id: str) -> Optional[ScrapedBid]:
        """
        Get detailed information for a specific bid.
        
        Args:
            bid_id: The bid identifier
            
        Returns:
            ScrapedBid with full details, or None if not found
        """
        pass
    
    def filter_by_category(
        self, 
        bids: List[ScrapedBid], 
        categories: List[str]
    ) -> List[ScrapedBid]:
        """
        Filter bids by category keywords.
        
        Args:
            bids: List of scraped bids
            categories: Category keywords to filter by
            
        Returns:
            Filtered list of bids
        """
        if not categories:
            return bids
        
        filtered = []
        category_lower = [c.lower() for c in categories]
        
        for bid in bids:
            bid_text = f"{bid.title} {bid.category or ''} {bid.department}".lower()
            if any(cat in bid_text for cat in category_lower):
                filtered.append(bid)
        
        return filtered


# Common category filters for consulting-relevant bids
CONSULTING_CATEGORIES = [
    "consultancy",
    "consulting",
    "advisory",
    "professional services",
    "management",
    "IT services",
    "digital",
    "software",
    "technology",
    "cyber",
    "training",
    "capacity building",
    "project management",
    "PMC",
    "DPR",
    "feasibility",
    "study",
    "assessment",
    "audit",
    "evaluation",
]

DEFENCE_CATEGORIES = [
    "defence",
    "defense",
    "military",
    "army",
    "navy",
    "air force",
    "ordnance",
    "ammunition",
    "security",
    "strategic",
]


def is_defence_organization(department: str) -> bool:
    """
    Check if a department/organization is from Ministry of Defence.
    
    Args:
        department: The department or organization name from the bid
        
    Returns:
        True if the organization is a MoD organization or DPSU
    """
    try:
        from config import ALL_DEFENCE_ORGANIZATIONS, DEFENCE_ORG_KEYWORDS
    except ImportError:
        # Fallback if config import fails
        return False
    
    if not department:
        return False
    
    dept_lower = department.lower()
    
    # Check against full organization names (case-insensitive partial match)
    for org in ALL_DEFENCE_ORGANIZATIONS:
        org_lower = org.lower()
        # Check if key parts of the org name appear in the department
        org_parts = [p.strip() for p in org_lower.split(',')[0].split('(')[0].split() if len(p) > 3]
        if len(org_parts) >= 2:
            # Match if at least 2 significant words match
            matches = sum(1 for part in org_parts if part in dept_lower)
            if matches >= 2:
                return True
        # Direct substring match
        if org_lower in dept_lower or dept_lower in org_lower:
            return True
    
    # Check against short keywords
    for keyword in DEFENCE_ORG_KEYWORDS:
        if keyword.lower() in dept_lower:
            return True
    
    return False


def filter_defence_bids(bids: list) -> list:
    """
    Filter bids to include only those from MoD organizations.
    
    Args:
        bids: List of ScrapedBid objects
        
    Returns:
        Filtered list containing only defence-related bids
    """
    defence_bids = []
    for bid in bids:
        if is_defence_organization(bid.department):
            defence_bids.append(bid)
    return defence_bids

