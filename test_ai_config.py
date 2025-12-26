
import logging
import google.generativeai as genai
from ai_analyzer import analyze_bid_complete, GeminiAnalyzer

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

def test_ai():
    print("Testing AI configuration...")

    # List available models
    try:
        print("Listing available models...")
        with open("models.txt", "w") as f:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(f"{m.name}\n")
        print("Models saved to models.txt")
    except Exception as e:
        print(f"Failed to list models: {e}")
    
    # 1. Test basic connectivity
    try:
        analyzer = GeminiAnalyzer()
        response = analyzer._call_gemini("Say 'Hello World' if you can hear me.")
        print(f"Basic connectivity test: {response}")
    except Exception as e:
        print(f"Basic connectivity failed: {e}")
        return

    # 2. Test Bid Analysis
    test_bid = {
        "Bid Number": "TEST/2024/001",
        "Items": "Consultancy for Digital Transformation Strategy",
        "Department": "Ministry of Tech",
        "End Date": "2025-01-01"
    }
    
    print("\nAnalyzing test bid...")
    result = analyze_bid_complete(test_bid)
    print(f"CFS Score: {result['cfs']['score']}")
    print(f"Verdict: {result['cfs']['verdict']}")
    print(f"Reasoning: {result['cfs']['reasoning']}")

if __name__ == "__main__":
    test_ai()
