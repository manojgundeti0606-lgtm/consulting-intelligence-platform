import requests
import time
import re
import json

BASE_URL = "https://bidplus.gem.gov.in"
ALL_BIDS_URL = f"{BASE_URL}/all-bids"
API_URL = f"{BASE_URL}/all-bids-data"

def test_connectivity():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": ALL_BIDS_URL,
        "Origin": BASE_URL,
        "X-Requested-With": "XMLHttpRequest"
    })

    print("1. Fetching Main Page for CSRF...")
    start = time.time()
    try:
        resp = session.get(ALL_BIDS_URL, timeout=10)
        print(f"   Status: {resp.status_code}, Time: {time.time()-start:.2f}s")
        match = re.search(r"'csrf_bd_gem_nk':\s*'([^']+)'", resp.text)
        if match:
            csrf = match.group(1)
            print(f"   CSRF Token: {csrf[:10]}...")
        else:
            print("   ❌ CSRF Token NOT found")
            return
    except Exception as e:
        print(f"   ❌ Error fetching main page: {e}")
        return

    print("\n2. hitting API Endpoint...")
    payload = {
        "param": {"searchBid": "", "searchType": "basic"},
        "filter": {"bidStatusType": "ongoing_bids", "byType": "all", "highBidValue": "", "sort": "Bid-Number-Newest"},
        "page": 1
    }
    data = {'payload': json.dumps(payload), 'csrf_bd_gem_nk': csrf}
    
    start = time.time()
    try:
        print("   Sending POST request...")
        resp = session.post(API_URL, data=data, timeout=30)
        print(f"   Status: {resp.status_code}, Time: {time.time()-start:.2f}s")
        if resp.status_code == 200:
            try:
                json_resp = resp.json()
                docs = json_resp.get('response', {}).get('response', {}).get('docs', [])
                print(f"   ✅ API Success! Found {len(docs)} bids.")
                if docs:
                    print(f"   First Bid: {docs[0].get('b_bid_number')} - {docs[0].get('final_end_date_sort')}")
            except Exception as e:
                print(f"   ❌ JSON Decode Error: {e}")
                print(f"   Response Preview: {resp.text[:200]}")
        else:
            print(f"   ❌ API Failed: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error hitting API: {e}")

if __name__ == "__main__":
    test_connectivity()
