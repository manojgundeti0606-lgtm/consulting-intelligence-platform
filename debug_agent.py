from agent_scheduler import CIPAgent
import sys
import os

# Ensure API key is set (print status, don't print key)
if os.getenv('GOOGLE_API_KEY'):
    print("✅ GOOGLE_API_KEY is found.")
else:
    print("❌ GOOGLE_API_KEY is MISSING.")

def test_agent():
    print("--- Testing Agent Daily Intelligence Run ---")
    agent = CIPAgent()
    try:
        # This runs scraping AND AI analysis
        count = agent.daily_intelligence_run()
        print(f"Agent run complete. Found {count} high-fit opportunities.")
    except Exception as e:
        print(f"ERROR in Agent Run: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()
