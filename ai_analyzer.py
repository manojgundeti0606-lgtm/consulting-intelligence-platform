"""
AI Analyzer Module - Gemini Integration
Provides consulting fit scoring, go/no-go analysis, and executive summaries

This module integrates with Google's Gemini AI to analyze government bids
and determine their fit for consulting firms. Key features:
- Consulting Fit Score (CFS) calculation
- Go/No-Go decision matrix
- Executive summary generation

Author: Manoj Gundeti
Last Updated: 2025-12-26
"""

# TODO: CodeRabbit - Please review this module for:
# - Error handling completeness
# - API rate limiting best practices  
# - Security considerations for API key handling
# - Code quality and maintainability

import os
import json
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from config import AI_CONFIG, FIRM_PROFILE, CONSULTING_TAXONOMY

# Load environment variables
load_dotenv()

# Create Gemini client
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))


class GeminiAnalyzer:
    """Wrapper for Gemini AI analysis functions"""
    
    def __init__(self):
        self.model_name = AI_CONFIG['model']
        # Remove 'models/' prefix if present for new SDK
        if self.model_name.startswith('models/'):
            self.model_name = self.model_name[7:]
        
        self.config = types.GenerateContentConfig(
            temperature=AI_CONFIG['temperature'],
            max_output_tokens=AI_CONFIG['max_tokens']
        )
    
    def _call_gemini(self, prompt: str, retry_count: int = 0) -> Optional[str]:
        """Call Gemini API with retry logic"""
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.config
            )
            return response.text
        except Exception as e:
            if retry_count < AI_CONFIG['retry_attempts']:
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._call_gemini(prompt, retry_count + 1)
            else:
                print(f"Gemini API Error: {e}")
                return None


def calculate_consulting_fit_score(bid_data: Dict, firm_profile: Dict = FIRM_PROFILE) -> Dict:
    """
    Calculates Consulting Fit Score (CFS) for a bid
    
    Args:
        bid_data: Dictionary containing bid information
        firm_profile: Firm's expertise and preferences
    
    Returns:
        Dict with score (0-100), verdict, and reasoning
    """
    analyzer = GeminiAnalyzer()
    
    # Prepare context
    bid_title = bid_data.get('Bid Number', 'N/A')
    items = bid_data.get('Items', '')
    department = bid_data.get('Department', '')
    
    # Build expertise list
    expertise_str = ", ".join(firm_profile['expertise_areas'][:10])
    industries_str = ", ".join(firm_profile['industries'][:8])
    
    prompt = f"""You are analyzing a government bid for EY Consulting, a leading management consulting firm.

**Firm Profile:**
- Core Expertise: {expertise_str}
- Target Industries: {industries_str}
- Focus: Strategy, Digital Transformation, Technology Consulting, Public Sector

**Bid Details:**
- Bid Number: {bid_title}
- Category/Items: {items}
- Department: {department}

**Task:**
Analyze if this bid is a good fit for EY Consulting. Score from 0-100 where:
- 80-100: Strong Fit (core expertise, high strategic value)
- 50-79: Marginal Fit (some alignment, worth considering)
- 0-49: Out of Scope (procurement/goods, not consulting, wrong domain)

**Output Format (JSON only):**
{{
  "score": <number 0-100>,
  "verdict": "<Strong Fit|Marginal Fit|Out of Scope>",
  "reasoning": "<2-3 sentence explanation focusing on why it matches or doesn't match EY's consulting capabilities>"
}}

Provide ONLY the JSON, no additional text."""

    response = analyzer._call_gemini(prompt)
    
    if response:
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
                return result
            else:
                # Fallback if JSON parsing fails
                return {
                    "score": 50,
                    "verdict": "Marginal Fit",
                    "reasoning": "Unable to analyze - insufficient information"
                }
        except json.JSONDecodeError:
            return {
                "score": 50,
                "verdict": "Marginal Fit",
                "reasoning": "Unable to analyze - parsing error"
            }
    else:
        return {
            "score": 0,
            "verdict": "Analysis Failed",
            "reasoning": "Gemini API unavailable"
        }


def generate_go_no_go_matrix(bid_data: Dict, sow_text: str = "", firm_profile: Dict = FIRM_PROFILE) -> Dict:
    """
    Analyzes bid for Go/No-Go decision
    
    Args:
        bid_data: Bid information
        sow_text: Scope of Work extracted from PDF (if available)
        firm_profile: Firm configuration
    
    Returns:
        Dict with flags (GREEN/YELLOW/RED) and recommendations
    """
    analyzer = GeminiAnalyzer()
    
    bid_number = bid_data.get('Bid Number', 'N/A')
    items = bid_data.get('Items', '')
    department = bid_data.get('Department', '')
    end_date = bid_data.get('End Date', '')
    
    # Calculate days to deadline
    from datetime import datetime
    try:
        deadline = datetime.strptime(end_date, '%Y-%m-%d')
        today = datetime.now()
        days_left = (deadline - today).days
        timeline_flag = "RED" if days_left < 7 else "YELLOW" if days_left < 14 else "GREEN"
    except:
        days_left = "Unknown"
        timeline_flag = "YELLOW"
    
    prompt = f"""You are a bid qualification analyst for EY Consulting.

**Bid Information:**
- Bid: {bid_number}
- Category: {items}
- Department: {department}
- Days to Deadline: {days_left}

**Scope of Work (if available):**
{sow_text[:1000] if sow_text else "Not extracted yet"}

**Task:**
Assess this bid for a GO/NO-GO decision. Analyze:
1. **Eligibility**: Any red flags in requirements (turnover, experience, certifications)?
2. **Timeline**: Is {days_left} days enough to prepare a quality proposal?
3. **Technical Fit**: Does the technology/domain match EY's capabilities?

**Output Format (JSON only):**
{{
  "eligibility_flag": "<GREEN|YELLOW|RED>",
  "timeline_flag": "<GREEN|YELLOW|RED>",
  "technical_flag": "<GREEN|YELLOW|RED>",
  "overall_recommendation": "<GO|MAYBE|NO-GO>",
  "key_concerns": "<1-2 sentence summary of main risks or blockers>",
  "opportunities": "<1 sentence on why this could be valuable if pursued>"
}}

Provide ONLY the JSON."""

    response = analyzer._call_gemini(prompt)
    
    if response:
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
                result['timeline_flag'] = timeline_flag  # Override with calculated value
                return result
        except json.JSONDecodeError:
            pass
    
    # Fallback
    return {
        "eligibility_flag": "YELLOW",
        "timeline_flag": timeline_flag,
        "technical_flag": "YELLOW",
        "overall_recommendation": "MAYBE",
        "key_concerns": "Unable to analyze - limited information",
        "opportunities": "Requires manual review"
    }


def generate_executive_summary(sow_text: str, bid_data: Dict) -> Dict:
    """
    Generates executive summary of the bid
    
    Args:
        sow_text: Full scope of work text
        bid_data: Bid metadata
    
    Returns:
        Dict with The Ask, Key Deliverables, and Evaluation Criteria
    """
    analyzer = GeminiAnalyzer()
    
    bid_number = bid_data.get('Bid Number', 'N/A')
    items = bid_data.get('Items', '')
    
    prompt = f"""You are summarizing a government bid for a busy executive.

**Bid:** {bid_number}
**Category:** {items}

**Full Scope of Work:**
{sow_text[:2000] if sow_text else "Not available - use category/items to infer"}

**Task:**
Create a 30-second executive summary with:
1. **The Ask**: ONE sentence describing what the client actually wants
2. **Key Deliverables**: Top 3 outputs (e.g., reports, systems, trainings)
3. **Evaluation Criteria**: How the winner is chosen (L1/QCBS/Technical scoring)

**Output Format (JSON only):**
{{
  "the_ask": "<single sentence>",
  "key_deliverables": ["<deliverable 1>", "<deliverable 2>", "<deliverable 3>"],
  "evaluation_criteria": "<brief description of selection method>"
}}

Provide ONLY the JSON."""

    response = analyzer._call_gemini(prompt)
    
    if response:
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except json.JSONDecodeError:
            pass
    
    # Fallback
    return {
        "the_ask": f"Project related to {items}",
        "key_deliverables": ["To be determined from bid document"],
        "evaluation_criteria": "Not specified"
    }


def analyze_bid_complete(bid_data: Dict, sow_text: str = "", pdf_path: str = None) -> Dict:
    """
    Runs complete AI analysis on a bid
    
    Args:
        bid_data: Bid information
        sow_text: Scope of Work text (optional, legacy)
        pdf_path: Path to local PDF file (for Virtual User)
    
    Returns:
        Complete analysis with CFS, Go/No-Go, and Summary
    """
    print(f"Analyzing bid: {bid_data.get('Bid Number')}...")
    
    # Virtual User Step: If PDF exists, read it "manually"
    virtual_user_summary = ""
    if pdf_path and os.path.exists(pdf_path):
        from virtual_agent import BidReaderAgent
        print(f"Virtual User: Reading document {os.path.basename(pdf_path)}...")
        try:
            agent = BidReaderAgent(pdf_path)
            virtual_user_summary = agent.summarize_sow()
            print("Virtual User: SOW Summary generated.")
        except Exception as e:
            print(f"Virtual User Error: {e}")
            virtual_user_summary = f"Error reading document: {e}"
    
    # Use virtual user summary if available, otherwise fallback to provided text
    final_sow_text = virtual_user_summary if virtual_user_summary else sow_text

    # Calculate Consulting Fit Score
    cfs_result = calculate_consulting_fit_score(bid_data)
    
    # Generate Go/No-Go Matrix
    gng_result = generate_go_no_go_matrix(bid_data, final_sow_text)
    
    # Generate Executive Summary (only if CFS > 50)
    if cfs_result.get('score', 0) >= 50:
        summary_result = generate_executive_summary(final_sow_text, bid_data)
    else:
        summary_result = {
            "the_ask": "Out of scope - analysis skipped",
            "key_deliverables": [],
            "evaluation_criteria": "N/A"
        }
    
    return {
        "bid_number": bid_data.get('Bid Number'),
        "cfs": cfs_result,
        "go_no_go": gng_result,
        "executive_summary": summary_result,
        "sow_summary": final_sow_text, # data from Virtual User
        "analyzed_at": time.strftime('%Y-%m-%d %H:%M:%S')
    }

