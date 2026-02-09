import requests
import json
import re
import time

BASE_URL = "https://bidplus.gem.gov.in"
API_URL = f"{BASE_URL}/all-bids-data"
ALL_BIDS_URL = f"{BASE_URL}/all-bids"

def get_csrf(session):
    resp = session.get(ALL_BIDS_URL)
    match = re.search(r"'csrf_bd_gem_nk':\s*'([^']+)'", resp.text)
    return match.group(1) if match else None

def test_sort():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": ALL_BIDS_URL,
        "Origin": BASE_URL,
        "X-Requested-With": "XMLHttpRequest"
    })
    
    print("Fetching CSRF...")
    csrf = get_csrf(session)
    if not csrf:
        print("No CSRF")
        return

    sort_keys = ["Bid-Number-Newest", "Bid-Start-Date-Latest", ""]
    
    for sort_key in sort_keys:
        print(f"\nEvaluating Sort Key: '{sort_key}'")
        payload = {
            "param": {"searchBid": "manpower", "searchType": "fullText"},
            "filter": {
                "bidStatusType": "ongoing_bids",
                "byType": "all",
                "highBidValue": "",
                "sort": sort_key
            }
        }
        data = {'payload': json.dumps(payload), 'csrf_bd_gem_nk': csrf}
        
        try:
            resp = session.post(API_URL, data=data, timeout=30)
            if resp.status_code == 200:
                docs = resp.json().get('response', {}).get('response', {}).get('docs', [])
                if docs:
                    first = docs[0]
                    start_date = str(first.get('final_start_date_sort', ''))
                    print(f"  Top Result Date: {start_date}")
                    bid_no = first.get('b_bid_number', '')
                    print(f"  Bid No: {bid_no}")
                else:
                    print("  No results found.")
            else:
                print(f"  Error: {resp.status_code}")
        except Exception as e:
            print(f"  Exception: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_sort()
