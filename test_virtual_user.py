
import os
import sys
from unittest.mock import MagicMock, patch
from virtual_agent import BidReaderAgent

def create_mock_pdf():
    # Create pages mimicking a real bid
    pages = []
    
    # Page 1-3: Intro
    for i in range(3):
        p = MagicMock()
        p.extract_text.return_value = f"This is page {i+1}. Introduction and general terms."
        pages.append(p)
        
    # Page 4: SOW Start
    p4 = MagicMock()
    p4.extract_text.return_value = "SECTION 3: SCOPE OF WORK\n\nThe vendor shall provide 500 laptops."
    pages.append(p4)
    
    # Page 5: SOW Content
    p5 = MagicMock()
    p5.extract_text.return_value = "Specifications: i7 processor, 16GB RAM. Delivery within 30 days."
    pages.append(p5)
    
    # Page 6: SOW End / New Section
    p6 = MagicMock()
    p6.extract_text.return_value = "SECTION 4: PAYMENT TERMS\n\nPayment will be made 100% after delivery."
    pages.append(p6)
    
    mock_pdf = MagicMock()
    mock_pdf.pages = pages
    mock_pdf.__enter__.return_value = mock_pdf
    mock_pdf.__exit__.return_value = None
    return mock_pdf

def test_virtual_user_logic():
    print("Testing Virtual User Logic (Mocked PDF)...")
    
    # Patch pdfplumber.open and os.path.exists
    with patch('pdfplumber.open') as mock_open:
        with patch('os.path.exists', return_value=True):
            mock_open.return_value = create_mock_pdf()
            
            # Test file path doesn't matter since we mock open
            agent = BidReaderAgent("dummy.pdf")
            
            # Patch internal LLM calls to avoid API costs during test/predictable output
            # identifying SOW start
            original_is_sow_start = agent._is_sow_start
            agent._is_sow_start = MagicMock(side_effect=lambda text: "SCOPE OF WORK" in text)
            
            # identifying SOW end
            original_is_new_section = agent._is_new_section
            agent._is_new_section = MagicMock(side_effect=lambda text: "SECTION 4" in text)
            
            # summarizing
            agent.summarizer_model.generate_content = MagicMock()
            agent.summarizer_model.generate_content.return_value.text = "Mock Summary: Supply 500 laptops with i7/16GB."
    
            print("\n--- Step 1: Find SOW Boundary ---")
            start, end = agent.find_sow_boundary()
            print(f"Result: Start={start+1}, End={end+1}")
            
            # Verification
            # Page 4 is index 3. Page 6 is index 5.
            # Logic: Start found at index 3.
            # Matches "SECTION 3" -> _is_sow_start=True
            # Iterate > 3. Index 4 (Page 5) -> "Specifications" -> _is_new_section=False
            # Index 5 (Page 6) -> "SECTION 4" -> _is_new_section=True -> End found.
            
            expected_start = 3
            expected_end = 5 
            
            if start == expected_start and end == expected_end:
                print("SUCCESS: Boundary detection logic works.")
            else:
                print(f"FAILURE: Expected {expected_start}-{expected_end}, got {start}-{end}")
    
            print("\n--- Step 2: Summarize ---")
            summary = agent.summarize_sow()
            print("Summary Result:", summary)
            
            if "Mock Summary" in summary:
                print("SUCCESS: Summarization flow works.")
            else:
                print("FAILURE: Summarization didn't return expected mock.")

if __name__ == "__main__":
    test_virtual_user_logic()
