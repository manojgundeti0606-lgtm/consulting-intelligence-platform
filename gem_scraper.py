import requests
import re
import json
import csv
import time
import os
import random
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from config import (
    CONSULTING_TAXONOMY, KEYWORD_EXPANSIONS, SCRAPING_CONFIG,
    FIRM_PROFILE
)

# Configuration
BASE_URL = "https://bidplus.gem.gov.in"
ALL_BIDS_URL = f"{BASE_URL}/all-bids"
API_URL = f"{BASE_URL}/all-bids-data"


def filter_new_bids(bids: List[Dict], db=None) -> Tuple[List[Dict], List[Dict]]:
    """
    Filters bids to separate new bids from already-seen bids.
    
    Args:
        bids: List of scraped bids
        db: Optional CIPDatabase instance for checking existing bids
        
    Returns:
        Tuple of (new_bids, existing_bids)
    """
    if db is None:
        try:
            from database import CIPDatabase
            db = CIPDatabase()
        except ImportError:
            # No database, return all as new
            return (bids, [])
    
    existing_bid_numbers: Set[str] = set()
    
    # Get all existing bid numbers from database
    try:
        all_db_bids = db.get_all_bids(limit=1000)  # Get recent bids for deduplication
        existing_bid_numbers = {b.get('bid_number') or b.get('Bid Number') for b in all_db_bids}
    except (AttributeError, TypeError) as e:
        # Log the specific error for debugging
        print(f"Warning: Could not fetch existing bids for deduplication: {e}")
    
    new_bids = []
    existing_bids = []
    
    for bid in bids:
        bid_num = bid.get('Bid Number', '')
        if bid_num in existing_bid_numbers:
            existing_bids.append(bid)
        else:
            new_bids.append(bid)
    
    return (new_bids, existing_bids)


def get_csrf_token(session):
    # print("Fetching main page to get CSRF token...")
    try:
        response = session.get(ALL_BIDS_URL)
        response.raise_for_status()
        
        match = re.search(r"'csrf_bd_gem_nk':\s*'([^']+)'", response.text)
        if match:
            return match.group(1)
        else:
            raise ValueError("CSRF token not found in page source")
    except Exception as e:
        print(f"Error getting CSRF token: {e}")
        return None


def expand_keywords(keyword: str) -> List[str]:
    """
    Expands keywords with semantic synonyms
    
    Args:
        keyword: Base search keyword
    
    Returns:
        List of keywords including expansions
    """
    if not keyword:
        return []
    
    keywords = [keyword]
    keyword_lower = keyword.lower()
    
    # Check for exact matches in expansion mappings
    for base_term, expansions in KEYWORD_EXPANSIONS.items():
        if base_term in keyword_lower:
            keywords.extend(expansions)
            break
    
    return list(set(keywords))  # Remove duplicates


def is_consulting_bid(bid_data: Dict) -> Tuple[bool, Optional[str]]:
    """
    Determines if a bid is consulting-related using taxonomy
    
    Args:
        bid_data: Bid information dictionary
    
    Returns:
        Tuple of (is_consulting, category_name)
    """
    items = bid_data.get('Items', '').lower()
    dept = bid_data.get('Department', '').lower()
    bid_number = bid_data.get('Bid Number', '').lower()
    
    # Combine all text for analysis
    full_text = f"{items} {dept} {bid_number}"
    
    # Check against each taxonomy category
    for category, rules in CONSULTING_TAXONOMY.items():
        # Check primary keywords
        for keyword in rules['primary_keywords']:
            if keyword.lower() in full_text:
                # Check for exclusions
                excluded = False
                for exclude_word in rules['exclude_keywords']:
                    if exclude_word.lower() in full_text:
                        excluded = True
                        break
                
                if not excluded:
                    # Check for secondary context (if defined)
                    if rules['secondary_context']:
                        for context_word in rules['secondary_context']:
                            if context_word.lower() in full_text:
                                return (True, category)
                    else:
                        return (True, category)
    
    return (False, None)


def scrape_bids(keywords="", from_date="", to_date="", max_pages=None, consulting_only=True, **kwargs):
    """
    Enhanced bid scraper with consulting taxonomy filtering
    
    Args:
        keywords: Search keywords
        from_date: Date filter (YYYY-MM-DD)
        to_date: Date filter (YYYY-MM-DD)
        max_pages: Maximum pages to scrape (defaults to config)
        consulting_only: Filter for consulting bids only
        **kwargs: Additional options like date_filter_type ('start' or 'end')
    
    Returns:
        List of bid dictionaries
    """
    if max_pages is None:
        max_pages = SCRAPING_CONFIG['max_pages']
    
    # Get retry configuration
    retry_attempts = SCRAPING_CONFIG['retry_attempts']
    retry_backoff = SCRAPING_CONFIG['retry_backoff']
    
    # Determine date filter type
    date_filter_type = kwargs.get('date_filter_type', 'end')

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": ALL_BIDS_URL,
        "Origin": BASE_URL,
        "X-Requested-With": "XMLHttpRequest"
    })

    csrf_token = get_csrf_token(session)
    if not csrf_token:
        return []

    # Expand keywords
    search_terms = expand_keywords(keywords) if keywords else [""]
    print(f"Searching for terms: {search_terms}")

    all_bids_dict = {} # Use dict to deduplicate by Bid Number

    for term in search_terms:
        print(f"Scraping for keyword: '{term}'")
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break

            # Construct payload
            payload = {
                "param": {
                    "searchBid": term,
                    "searchType": "fullText" if term else "basic"
                },
                "filter": {
                    "bidStatusType": "ongoing_bids",
                    "byType": "all",
                    "highBidValue": "",
                    "sort": "Bid-Number-Newest"  # Sort by bid number for consistent results
                }
            }
            
            # Use server-side filter for end date if requested
            if date_filter_type == 'end' and from_date and to_date:
                payload['filter']['byEndDate'] = {
                    "from": from_date,
                    "to": to_date
                }
            
            data = {
                'payload': json.dumps(payload),
                'csrf_bd_gem_nk': csrf_token
            }
            
            if page > 1:
                payload['page'] = page
                data['payload'] = json.dumps(payload)

            # Retry logic with exponential backoff
            for attempt in range(retry_attempts):
                try:
                    response = session.post(API_URL, data=data, timeout=30)
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get('code') != 200:
                        print(f"API returned error code: {result.get('code')}")
                        break
                        
                    docs = result.get('response', {}).get('response', {}).get('docs', [])
                    if not docs:
                        break
                        
                    for doc in docs:
                        # Local start date filter
                        if date_filter_type == 'start' and from_date:
                            s_date_raw = doc.get('final_start_date_sort', [''])[0] if isinstance(doc.get('final_start_date_sort'), list) else doc.get('final_start_date_sort', '')
                            # from_date is YYYY-MM-DD, s_date_raw is YYYY-MM-DDTHH:MM:SSZ
                            if s_date_raw and s_date_raw < from_date:
                                # Older than our window, can skip (but don't break yet if out of order)
                                continue
                            if to_date and s_date_raw > to_date + "T23:59:59Z":
                                continue

                        b_id_raw = doc.get('b_id')
                        if isinstance(b_id_raw, list) and len(b_id_raw) > 0:
                            b_id = str(b_id_raw[0])
                        else:
                            b_id = str(b_id_raw)
                        
                        # Handle bid number safely
                        bid_no_raw = doc.get('b_bid_number', '')
                        if isinstance(bid_no_raw, list) and len(bid_no_raw) > 0:
                            bid_number = str(bid_no_raw[0])
                        else:
                            bid_number = str(bid_no_raw)
                        
                        # Handle category name safely
                        cat_name = doc.get('b_category_name', [''])
                        if isinstance(cat_name, list) and len(cat_name) > 0:
                            items = str(cat_name[0])
                        else:
                            items = str(cat_name)
                            
                        # Handle quantity safely
                        qty_raw = doc.get('b_total_quantity', '')
                        if isinstance(qty_raw, list) and len(qty_raw) > 0:
                            quantity = str(qty_raw[0])
                        else:
                            quantity = str(qty_raw)
                        
                        dept_name = str(doc.get('ba_official_details_deptName', ''))
                        min_name = str(doc.get('ba_official_details_minName', ''))
                        department = f"{min_name}, {dept_name}".strip(', ')
                        
                        start_date = str(doc.get('final_start_date_sort', ''))
                        end_date = str(doc.get('final_end_date_sort', ''))
                        
                        doc_lbl = 'showbidDocument'
                        if doc.get('b_bid_type') == 5:
                            doc_lbl = 'showdirectradocumentPdf'
                        elif doc.get('b_bid_type') == 2:
                            doc_lbl = 'showradocumentPdf'
                            if doc.get('b_eval_type', 0) > 0:
                                doc_lbl = 'list-ra-schedules'
                        
                        document_link = f"{BASE_URL}/{doc_lbl}/{b_id}"
                        
                        bid_data = {
                            'Bid Number': bid_number,
                            'Items': items,
                            'Quantity': quantity,
                            'Department': department,
                            'Start Date': start_date,
                            'End Date': end_date,
                            'Document Link': document_link,
                            'Matched Term': term # Track which term matched
                        }
                        
                        # Apply consulting taxonomy filter
                        if consulting_only:
                            is_consulting, category = is_consulting_bid(bid_data)
                            if is_consulting:
                                bid_data['Category'] = category
                                all_bids_dict[bid_number] = bid_data
                        else:
                            all_bids_dict[bid_number] = bid_data
                        
                    # Success - break retry loop
                    break
                        
                except Exception as e:
                    print(f"Error fetching page {page} for term '{term}' (attempt {attempt + 1}/{retry_attempts}): {e}")
                    if attempt < retry_attempts - 1:
                        time.sleep(retry_backoff ** attempt)
                    else:
                        break
            
            # Break outer loop if no docs found (optimization)
            if 'docs' in locals() and not docs:
                break
            
            # Rate limiting
            if not max_pages or page < max_pages:
                sleep_time = random.uniform(
                    SCRAPING_CONFIG['rate_limit_min'],
                    SCRAPING_CONFIG['rate_limit_max']
                )
                time.sleep(sleep_time)
            
            page += 1

    # Sort results by bid number (descending) for consistent order
    sorted_bids = sorted(
        all_bids_dict.values(),
        key=lambda x: x.get('Bid Number', ''),
        reverse=True
    )
    
    return sorted_bids



def download_document(url, save_dir="downloads", bid_data=None):
    """
    Downloads bid document with enhanced folder structure and naming
    
    Args:
        url: Document URL
        save_dir: Base directory for downloads
        bid_data: Optional bid information for smart naming
    
    Returns:
        Path to downloaded file or None if failed
    """
    from datetime import datetime
    
    # Create structured folder: downloads/{Year}/{Month}/{Bid_Number}/
    if bid_data:
        start_date = bid_data.get('Start Date', '')
        bid_number = bid_data.get('Bid Number', 'Unknown')
        
        try:
            dt = datetime.strptime(start_date, '%Y-%m-%d')
            year = str(dt.year)
            month = f"{dt.month:02d}"
        except (ValueError, TypeError):
            year = datetime.now().strftime('%Y')
            month = datetime.now().strftime('%m')
        
        # Create nested folder structure
        final_save_dir = os.path.join(save_dir, year, month, bid_number)
    else:
        final_save_dir = save_dir
    
    if not os.path.exists(final_save_dir):
        os.makedirs(final_save_dir)
    
    # Smart filename: [Bid_No]_[Short_Dept]_[Short_Title].pdf
    if bid_data:
        bid_number = bid_data.get('Bid Number', 'BID')
        dept = bid_data.get('Department', '')
        items = bid_data.get('Items', '')
        
        # Shorten department name (take first organization)
        dept_short = dept.split(',')[0][:30] if dept else "Dept"
        
        # Shorten items/title
        items_short = items[:40] if items else "Document"
        
        # Clean special characters
        dept_short = re.sub(r'[\\/*?:"<>|]', '', dept_short).strip()
        items_short = re.sub(r'[\\/*?:"<>|]', '', items_short).strip()
        bid_number = re.sub(r'[\\/*?:"<>|]', '', bid_number).strip()
        
        filename = f"{bid_number}_{dept_short}_{items_short}.pdf"
    else:
        filename = url.split('/')[-1] + ".pdf"
        filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    
    save_path = os.path.join(final_save_dir, filename)
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text content from a PDF file using pdfplumber
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    import pdfplumber
    
    text_content = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return "\n".join(text_content).strip()
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return ""


def extract_hyperlinks_from_pdf(pdf_path: str) -> List[str]:
    """
    Extracts all URIs from hyperlinks in a PDF
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of extracted URIs
    """
    import pdfplumber
    
    links = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                if hasattr(page, 'hyperlinks') and page.hyperlinks:
                    for link in page.hyperlinks:
                        if 'uri' in link:
                            links.append(link['uri'])
    except Exception as e:
        print(f"Error extracting links from PDF {pdf_path}: {e}")
    
    return list(set(links))  # Deduplicate
