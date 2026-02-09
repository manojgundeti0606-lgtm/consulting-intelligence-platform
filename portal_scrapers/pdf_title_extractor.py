"""
PDF Title Extractor using Gemini AI

Extracts tender titles from PDF documents using Gemini's URL reading capability.
This works for Goa Shipyard PDFs where direct download fails but browser access works.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logger = logging.getLogger(__name__)


def extract_title_from_pdf_url(pdf_url: str, fallback_title: str = "") -> str:
    """
    Use Gemini AI to extract the tender title from a PDF URL.
    
    Args:
        pdf_url: URL of the PDF document
        fallback_title: Title to return if extraction fails
        
    Returns:
        Extracted tender title or fallback
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No GOOGLE_API_KEY found, using fallback title")
        return fallback_title
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""Analyze this tender document and extract the main title/subject.
        
Document URL: {pdf_url}

Instructions:
1. Read the PDF document from the URL
2. Extract the main tender title or project name - NOT the tender number
3. Look for the subject line, project description, or scope of work title
4. Return ONLY the title/subject, nothing else
5. Keep it concise (max 100 characters)
6. If you cannot access the document, return "Unable to access"

Return format: Just the title text, no quotes or explanation."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=100,
            )
        )
        
        if response and response.text:
            title = response.text.strip()
            # Clean up common issues
            title = title.replace('"', '').replace("'", "")
            if title and len(title) > 5 and "unable to access" not in title.lower():
                logger.info(f"Extracted title: {title[:50]}...")
                return title[:150]
        
        return fallback_title
        
    except Exception as e:
        logger.error(f"Error extracting title from PDF: {e}")
        return fallback_title


def enhance_goa_shipyard_bid_title(bid: dict) -> dict:
    """
    Enhance a Goa Shipyard bid by extracting the actual tender title from PDF.
    
    Args:
        bid: Bid dictionary with 'Items' and 'Document Link' fields
        
    Returns:
        Updated bid dictionary with better title
    """
    source_portal = bid.get('Source Portal', '').lower()
    if source_portal != 'goa_shipyard':
        return bid
    
    doc_link = bid.get('Document Link', '')
    current_title = bid.get('Items', '')
    
    if not doc_link or not doc_link.endswith('.pdf'):
        return bid
    
    # Check if current title is just a generic one
    if 'goa shipyard gem tender' in current_title.lower():
        new_title = extract_title_from_pdf_url(doc_link, current_title)
        if new_title != current_title:
            bid['Items'] = f"GSL: {new_title}"
            bid['raw_data'] = bid.get('raw_data', {})
            bid['raw_data']['original_title'] = current_title
    
    return bid


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test with a Goa Shipyard PDF
    test_url = "https://goashipyard.in/assets/front/public/tender/GeM-Bidding-8311812.pdf"
    print(f"Testing PDF title extraction from: {test_url}")
    
    title = extract_title_from_pdf_url(test_url, "Fallback Title")
    print(f"Extracted title: {title}")
