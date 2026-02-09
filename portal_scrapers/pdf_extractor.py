"""
PDF Content Extractor for Tender Documents

Downloads PDF documents and extracts title/content information
to provide better tender titles for DPSU scrapers.

Author: Manoj Gundeti
"""

import io
import re
import logging
import requests
from typing import Optional, Dict, Any
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


class PDFTitleExtractor:
    """
    Extracts meaningful titles from tender PDF documents.
    
    Downloads the PDF and attempts to extract:
    1. PDF metadata (title, subject)
    2. First few lines of text content
    3. Key information like tender number, organization, etc.
    """
    
    def __init__(self, verify_ssl: bool = False):
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.verify = verify_ssl
        
        # Suppress SSL warnings if not verifying
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def extract_title(self, pdf_url: str, fallback_title: str = "") -> Dict[str, Any]:
        """
        Extract title and info from a PDF document.
        
        Args:
            pdf_url: URL of the PDF to download and parse
            fallback_title: Title to use if extraction fails
            
        Returns:
            Dict with 'title', 'description', 'tender_id', 'organization'
        """
        result = {
            'title': fallback_title,
            'description': '',
            'tender_id': '',
            'organization': '',
            'extracted': False
        }
        
        try:
            # Download PDF (limit to first 2MB to avoid long downloads)
            response = self.session.get(pdf_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Read up to 2MB
            content = b''
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                content += chunk
                if len(content) > 2 * 1024 * 1024:
                    break
            
            # Parse PDF
            pdf_reader = PdfReader(io.BytesIO(content))
            
            # Try to get metadata
            metadata = pdf_reader.metadata
            if metadata:
                if metadata.title and len(metadata.title) > 10:
                    result['title'] = metadata.title
                    result['extracted'] = True
                if metadata.subject:
                    result['description'] = metadata.subject
            
            # Extract text from first page
            if len(pdf_reader.pages) > 0:
                first_page_text = pdf_reader.pages[0].extract_text()
                if first_page_text:
                    result = self._parse_text_for_info(first_page_text, result)
            
        except requests.RequestException as e:
            logger.debug(f"Failed to download PDF {pdf_url}: {e}")
        except Exception as e:
            logger.debug(f"Failed to parse PDF {pdf_url}: {e}")
        
        return result
    
    def _parse_text_for_info(self, text: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse extracted text to find tender information."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Look for tender ID patterns
        tender_patterns = [
            r'Tender\s*(?:No|Number|ID)[\s:.-]*([A-Z0-9/-]+)',
            r'NIT\s*(?:No|Number)[\s:.-]*([A-Z0-9/-]+)',
            r'Bid\s*(?:No|Number)[\s:.-]*([A-Z0-9/-]+)',
            r'GEM/\d+/\d+/\d+',
            r'\d{7,}',  # Long numbers often are tender IDs
        ]
        
        for pattern in tender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['tender_id'] = match.group(1) if match.groups() else match.group(0)
                break
        
        # Look for organization
        org_patterns = [
            r'(?:Goa|GOA)\s*Shipyard\s*(?:Limited|Ltd)',
            r'(?:Department|Dept)\s*of\s*Defence\s*Production',
            r'(?:Ministry|Min)\s*of\s*Defence',
            r'(?:Indian|Hindustan)\s*Aeronautics',
            r'(?:GRSE|GSL|HAL|BDL|BHEL)',
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['organization'] = match.group(0)
                break
        
        # Use first meaningful line as title if we don't have one
        if not result['extracted'] or len(result['title']) < 20:
            for line in lines[:10]:
                # Skip very short lines or header text
                if len(line) > 20 and not any(skip in line.lower() for skip in 
                    ['page', 'confidential', 'date:', 'tender notice', 'request for']):
                    # Found a potential title
                    result['title'] = line[:150]
                    result['extracted'] = True
                    break
        
        # Build a better description from first few lines
        if not result['description']:
            meaningful_lines = [l for l in lines[:5] if len(l) > 10]
            result['description'] = ' '.join(meaningful_lines)[:300]
        
        return result


def enhance_bid_title(pdf_url: str, current_title: str, organization: str = "") -> str:
    """
    Convenience function to enhance a bid title using PDF content.
    
    Args:
        pdf_url: URL of the tender PDF
        current_title: Current title (used as fallback)
        organization: Organization name to prepend
        
    Returns:
        Enhanced title string
    """
    extractor = PDFTitleExtractor(verify_ssl=False)
    info = extractor.extract_title(pdf_url, current_title)
    
    if info['extracted']:
        title = info['title']
        if organization and not title.lower().startswith(organization.lower()):
            title = f"{organization}: {title}"
        return title
    
    return current_title


if __name__ == "__main__":
    # Test with a Goa Shipyard PDF
    logging.basicConfig(level=logging.INFO)
    
    test_url = "https://goashipyard.in/assets/front/public/tender/GeM-Bidding-8311812.pdf"
    print(f"Testing PDF extraction from: {test_url}")
    
    extractor = PDFTitleExtractor(verify_ssl=False)
    result = extractor.extract_title(test_url, "Fallback Title")
    
    print(f"Extracted: {result['extracted']}")
    print(f"Title: {result['title']}")
    print(f"Tender ID: {result['tender_id']}")
    print(f"Organization: {result['organization']}")
    print(f"Description: {result['description'][:100]}...")
