from ai_analyzer import analyze_bid_complete
import json
import os

def test_ai():
    print(f"API Key present: {bool(os.getenv('GOOGLE_API_KEY'))}")
    
    test_bid = {
        "Bid Number": "TEST/DEBUG/001",
        "Items": "Cloud Migration Services",
        "Department": "Ministry of Tech",
        "End Date": "2025-12-31"
    }
    
    print("Running analysis...")
    result = analyze_bid_complete(test_bid)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_ai()
