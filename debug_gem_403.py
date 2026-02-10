import requests
import re
import json

BASE_URL = "https://bidplus.gem.gov.in"
ALL_BIDS_URL = f"{BASE_URL}/all-bids"
API_URL = f"{BASE_URL}/all-bids-data"

def debug_gem():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": ALL_BIDS_URL,
        "Origin": BASE_URL,
        "X-Requested-With": "XMLHttpRequest"
    })

    print(f"Fetching {ALL_BIDS_URL}...")
    try:
        response = session.get(ALL_BIDS_URL, timeout=30)
        print(f"Main page status: {response.status_code}")
        response.raise_for_status()
        
        match = re.search(r"'csrf_bd_gem_nk':\s*'([^']+)'", response.text or "")
        if match:
            csrf_token = match.group(1)
            print(f"Found CSRF token: {csrf_token}")
        else:
            print("CSRF token not found in page source!")
            return

        payload = {
            "param": {
                "searchBid": "consultancy",
                "searchType": "fullText"
            },
            "filter": {
                "bidStatusType": "ongoing_bids",
                "byType": "all",
                "highBidValue": "",
                "sort": "Bid-Number-Newest"
            }
        }
        
        data = {
            'payload': json.dumps(payload),
            'csrf_bd_gem_nk': csrf_token
        }
        
        print(f"Posting to {API_URL}...")
        response = session.post(API_URL, data=data, timeout=30)
        print(f"API result status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            docs = result.get('response', {}).get('response', {}).get('docs', [])
            print(f"Successfully fetched {len(docs)} documents.")
            for doc in docs[:5]:
                b_no = doc.get('b_bid_number', '')
                s_date = doc.get('final_start_date_sort', '')
                print(f"  - {b_no}: Start Date = {s_date}")
        else:
            print(f"Error: {response.text[:500]}")

    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    debug_gem()
