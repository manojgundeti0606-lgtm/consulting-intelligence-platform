"""
Virtual Agent Module - Simulates a human reader for bid documents
"""

import os
import time
import json
import pdfplumber
from google import genai
from google.genai import types
from typing import Dict, List, Optional, Tuple
from config import AI_CONFIG

# Create client at module level
_client = None

def get_client():
    global _client
    if _client is None:
        if not os.getenv('GOOGLE_API_KEY'):
            from dotenv import load_dotenv
            load_dotenv()
        _client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
    return _client


class BidReaderAgent:
    """
    A virtual agent that reads bid documents like a human to find and extract
    specific sections (like Scope of Work) before analysis.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.is_valid_pdf = self._validate_pdf()
        self._setup_ai()
    
    def _validate_pdf(self) -> bool:
        """Check if the file is a valid PDF before processing."""
        if not os.path.exists(self.pdf_path):
            print(f"Virtual User: File not found: {self.pdf_path}")
            return False
        
        # Check file size (PDFs are typically > 1KB)
        file_size = os.path.getsize(self.pdf_path)
        if file_size < 100:
            print(f"Virtual User: File too small ({file_size} bytes) - likely not a valid PDF")
            return False
        
        # Check PDF magic bytes (header should start with %PDF-)
        try:
            with open(self.pdf_path, 'rb') as f:
                header = f.read(10)
                if not header.startswith(b'%PDF-'):
                    # Check if it's HTML (error page)
                    text_header = header.decode('utf-8', errors='ignore').lower()
                    if '<html' in text_header or '<!doctype' in text_header:
                        print("Virtual User: Downloaded file is HTML, not PDF (likely login/error page)")
                    else:
                        print(f"Virtual User: File doesn't start with PDF header: {header[:20]}")
                    return False
        except Exception as e:
            print(f"Virtual User: Error reading file header: {e}")
            return False
        
        # Try to open with pdfplumber to verify
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    print("Virtual User: PDF has no pages")
                    return False
            return True
        except Exception as e:
            error_msg = str(e)
            if "Root" in error_msg:
                print("Virtual User: Invalid PDF structure - file is corrupted or not a real PDF")
            else:
                print(f"Virtual User: Failed to open PDF: {e}")
            return False
        
    def _setup_ai(self):
        """Initialize Gemini model names for page analysis"""
        self.client = get_client()
        # Use configured fast model for scanning, smart model for summary
        fast_model = AI_CONFIG.get('fast_model', 'gemini-2.0-flash')
        main_model = AI_CONFIG['model']
        # Remove 'models/' prefix if present
        self.fast_model = fast_model[7:] if fast_model.startswith('models/') else fast_model
        self.summarizer_model = main_model[7:] if main_model.startswith('models/') else main_model

    def _get_page_text(self, page_num: int) -> str:
        """Extract text from a specific page (0-indexed)"""
        if not self.is_valid_pdf:
            return ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    return pdf.pages[page_num].extract_text() or ""
        except Exception as e:
            print(f"Error reading page {page_num}: {e}")
        return ""

    def find_sow_boundary(self) -> Tuple[int, int]:
        """
        Scans the document to find the start and end pages of the Scope of Work.
        Returns: (start_page_index, end_page_index)
        """
        # Return default range if PDF is invalid
        if not self.is_valid_pdf:
            return (0, 0)
        
        print(f"Virtual User: Scanning {os.path.basename(self.pdf_path)} for SOW...")
        
        start_page = -1
        end_page = -1
        
        # Heuristic: SOW is usually in the first 20 pages or after "Table of Contents"
        # We'll scan the first 30 pages to find headers
        max_scan_pages = 30
        
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            scan_limit = min(total_pages, max_scan_pages)
            
            for i in range(scan_limit):
                text = pdf.pages[i].extract_text()
                if not text:
                    continue
                    
                # Quick keyword check before expensive LLM call
                lower_text = text.lower()
                if "scope of work" in lower_text or "scope of supply" in lower_text or "technical specifications" in lower_text:
                    
                    # Ask LLM to confirm if this page STARTS the SOW
                    if start_page == -1:
                        if self._is_sow_start(text):
                            start_page = i
                            print(f"Virtual User: Found SOW start on page {i+1}")
                
                # If we found start, look for end (next section)
                if start_page != -1 and i > start_page:
                    if self._is_new_section(text):
                        end_page = i
                        print(f"Virtual User: Found SOW end on page {i+1}")
                        break
            
            # Fallback: If start found but no end, read next 5 pages
            if start_page != -1 and end_page == -1:
                end_page = min(start_page + 5, total_pages)
                
            # Fallback: If nothing found, assume first 5 pages contain summary info
            if start_page == -1:
                print("Virtual User: Could not locate explicit SOW section. Using default range.")
                start_page = 0
                end_page = min(5, total_pages)

        return start_page, end_page

    def _call_gemini(self, model_name: str, prompt: str, retry_count: int = 0) -> Optional[str]:
        """Call Gemini API with robust retry logic for 429 rate limits"""
        max_retries = 5
        base_delay = 5  # seconds
        
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                if retry_count < max_retries:
                    delay = base_delay * (2 ** retry_count) # 5, 10, 20, 40, 80
                    print(f"Virtual User: Rate limit hit. Retrying in {delay}s...")
                    time.sleep(delay)
                    return self._call_gemini(model_name, prompt, retry_count + 1)
                else:
                    return f"Error: Quota exceeded after {max_retries} retries."
            else:
                print(f"Virtual User Error: {e}")
                return None

    def _is_sow_start(self, text: str) -> bool:
        """Ask LLM if this text looks like the start of SOW"""
        prompt = f"""
        Does this text contain the START of a "Scope of Work", "Technical Specifications", or "Work Requirements" section?
        Ignore Table of Contents.
        
        Text:
        {text[:1000]}
        
        Answer YES or NO.
        """
        response = self._call_gemini(self.fast_model, prompt)
        return response and "YES" in response.strip().upper()

    def _is_new_section(self, text: str) -> bool:
        """Ask LLM if this text looks like a NEW major section (marking end of previous)"""
        prompt = f"""
        Does this text indicate the START of a NEW major section (like "Annexure", "Financial Bid", "General Terms")?
        This would mark the END of the previous section.
        
        Text:
        {text[:1000]}
        
        Answer YES or NO.
        """
        response = self._call_gemini(self.fast_model, prompt)
        return response and "YES" in response.strip().upper()

    def extract_sow_text(self, start_page: int, end_page: int) -> str:
        """Extracts text from the identified range"""
        text_content = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Add buffer if needed, but strict range is usually better to avoid noise
                for i in range(start_page, end_page):
                    if i < len(pdf.pages):
                        text = pdf.pages[i].extract_text()
                        if text:
                            text_content.append(text)
            return "\n".join(text_content)
        except Exception as e:
            print(f"Error extracting SOW text: {e}")
            return ""

    def summarize_sow(self) -> str:
        """
        Main method: Finds, extracts, and summarizes the SOW.
        """
        # Check if PDF was validated successfully
        if not self.is_valid_pdf:
            return "Error: The downloaded file is not a valid PDF document. This could be because:\n- The tender document requires login to the portal\n- The document link has expired\n- The portal returned an error page instead of the document\n\nPlease try downloading the document manually from the portal."
        
        if not os.path.exists(self.pdf_path):
            return "Error: Document not found locally."

        # Scan for boundary with delay to respect rate limits
        start, end = self.find_sow_boundary()
        
        # If boundary found or default used, extract text
        sow_text = self.extract_sow_text(start, end)
        
        if not sow_text or len(sow_text) < 50:
            return "Virtual User: Could not extract sufficient text for SOW summary."

        print(f"Virtual User: Reading {len(sow_text)} characters of SOW text...")
        
        prompt = f"""
        You are an expert technical consultant. 
        Read the following Scope of Work text extracted from a bid document.
        
        Task:
        1. Summarize the core requirements (What needs to be done/supplied?)
        2. List key quantities if mentioned.
        3. Identify any specific technical qualifications required.
        
        Scope of Work Text:
        {sow_text[:25000]}
        
        Output:
        Provide a clean, structured summary (bullet points preferred). Keep it under 300 words.
        """
        
        response = self._call_gemini(self.summarizer_model, prompt)
        return response if response else "Failed to generate summary due to API error."

if __name__ == "__main__":
    # Test block
    import sys
    if len(sys.argv) > 1:
        agent = BidReaderAgent(sys.argv[1])
        print(agent.summarize_sow())
