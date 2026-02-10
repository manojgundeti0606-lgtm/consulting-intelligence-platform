"""
Selenium-based DDP Tender Scraper

Scrapes tenders from https://www.ddpmod.gov.in/offerings/tenders-of-ddp
Uses Selenium to handle JavaScript-rendered content.

Author: Manoj Gundeti
"""

import logging
import re
import time
from datetime import datetime
from typing import List, Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException

from .base_scraper import BaseScraper, ScrapedBid, PortalType

logger = logging.getLogger(__name__)


class DDPSeleniumScraper(BaseScraper):
    """
    Selenium-based scraper for Department of Defence Production tenders.
    
    Handles JavaScript-rendered content that the basic requests scraper cannot access.
    """
    
    BASE_URL = "https://www.ddpmod.gov.in"
    TENDER_URL = "https://www.ddpmod.gov.in/offerings/tenders-of-ddp"
    
    def __init__(self, headless: bool = True):
        super().__init__(PortalType.DDP)
        self.headless = headless
        self.driver = None
    
    @property
    def portal_name(self) -> str:
        return "Department of Defence Production (Selenium)"
    
    @property
    def base_url(self) -> str:
        return self.BASE_URL
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with options."""
        if self.driver:
            return
        
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Suppress logging
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
    
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
        Scrape tenders from DDP website using Selenium.
        """
        self.logger.info("Scraping DDP tenders with Selenium...")
        bids = []
        
        try:
            self._init_driver()
            
            # Navigate to tender page
            self.driver.get(self.TENDER_URL)
            
            # Wait for page to load
            time.sleep(3)
            
            # Wait for content to appear
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                self.logger.warning("Timeout waiting for page load")
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Find PDF links
            pdf_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")
            self.logger.info(f"Found {len(pdf_links)} PDF links")
            
            for link in pdf_links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip() or link.get_attribute("title") or ""
                    
                    if not href or not text:
                        continue
                    
                    # Skip navigation links
                    nav_patterns = ['about', 'contact', 'home', 'team', 'policy']
                    if any(p in href.lower() for p in nav_patterns):
                        continue
                    
                    bid = self._create_bid(href, text)
                    if bid:
                        bids.append(bid)
                except Exception as e:
                    self.logger.debug(f"Error processing link: {e}")
            
            # Also look for tender tables/listings
            tender_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".tender-item, .tender-listing, tr[class*='tender'], div[class*='tender']"
            )
            self.logger.info(f"Found {len(tender_elements)} tender elements")
            
            for elem in tender_elements:
                try:
                    links = elem.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href")
                        text = elem.text.strip()[:200]
                        
                        if href and ('.pdf' in href.lower() or 'tender' in href.lower()):
                            bid = self._create_bid(href, text)
                            if bid:
                                bids.append(bid)
                except Exception as e:
                    self.logger.debug(f"Error processing tender element: {e}")
            
            self.logger.info(f"Scraped {len(bids)} tenders from DDP")
            
        except WebDriverException as e:
            self.logger.error(f"Selenium error scraping DDP: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error scraping DDP: {e}")
        finally:
            self._close_driver()
        
        return bids
    
    def _create_bid(self, href: str, text: str) -> Optional[ScrapedBid]:
        """Create a ScrapedBid from link info."""
        if not href:
            return None
        
        filename = href.split('/')[-1]
        title = text or filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        
        # Skip if title is too short or generic
        if len(title) < 5:
            return None
        
        # Add DDP prefix if not present
        if not title.lower().startswith('ddp') and not title.lower().startswith('defence'):
            title = f"DDP: {title}"
        
        # Extract date if present
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', title)
        end_date = date_match.group(1) if date_match else None
        
        bid_number = self._generate_bid_number(filename)
        
        return ScrapedBid(
            bid_number=bid_number,
            title=title[:200],
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
    
    def _generate_bid_number(self, identifier: str) -> str:
        """Generate a unique bid number from identifier."""
        clean = re.sub(r'[^\w\-]', '_', identifier)[:30]
        num_match = re.search(r'(\d{5,})', identifier)
        if num_match:
            return f"DDP/{num_match.group(1)}"
        return f"DDP/{clean}"
    
    def get_bid_details(self, bid_id: str) -> Optional[ScrapedBid]:
        """Get details for a specific bid."""
        return None


def scrape_ddp_selenium(headless: bool = True) -> List[Dict[str, Any]]:
    """Convenience function to scrape DDP tenders with Selenium."""
    scraper = DDPSeleniumScraper(headless=headless)
    bids = scraper.scrape_bids()
    return [bid.to_dict() for bid in bids]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bids = scrape_ddp_selenium(headless=False)
    print(f"Found {len(bids)} bids")
    for bid in bids[:5]:
        print(f"  - {bid.get('Items', 'No title')}")
