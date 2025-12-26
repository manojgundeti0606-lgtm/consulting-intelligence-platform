"""
Debug script to list all available Gemini models and test connectivity.
Run this script to diagnose API issues.
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')
print(f"API Key present: {bool(api_key)}")
if api_key:
    print(f"API Key (first 10 chars): {api_key[:10]}...")

if api_key:
    genai.configure(api_key=api_key)
    
    print("\n" + "="*50)
    print("AVAILABLE MODELS (supporting generateContent):")
    print("="*50)
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                print(f"  - {m.name}")
        print(f"\nTotal: {len(available_models)} models available")
    except Exception as e:
        print(f"Error listing models: {e}")
        available_models = []

    print("\n" + "="*50)
    print("TESTING MODEL CONNECTIVITY:")
    print("="*50)
    
    # Test the first few available models
    test_models = available_models[:5] if available_models else [
        "models/gemini-1.5-pro-latest",
        "models/gemini-1.5-flash-latest",
        "models/gemini-pro",
        "gemini-pro"
    ]
    
    for model_name in test_models:
        print(f"\nTesting: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'API working' in exactly two words.")
            print(f"  SUCCESS: {response.text.strip()[:80]}")
            break  # Stop after first success
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {str(e)[:100]}")
else:
    print("ERROR: No API key found in .env file!")
    print("Please add GOOGLE_API_KEY=your_key_here to .env")
