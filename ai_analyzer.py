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

import os
import json
import time
import random
import logging
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from config import AI_CONFIG, FIRM_PROFILE, CONSULTING_TAXONOMY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Module-level client cache (singleton pattern)
_gemini_client: Optional[genai.Client] = None


class APIKeyError(ValueError):
    """Raised when the GOOGLE_API_KEY is missing or invalid."""
    pass


class RateLimiter:
    """
    Token bucket rate limiter with jitter for API calls.
    Implements proactive throttling to prevent rate limit errors.
    Thread-safe with internal locking.
    """
    
    def __init__(self, calls_per_minute: int = 15, jitter_range: tuple = (0.5, 1.5)):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute  # seconds between calls
        self.jitter_range = jitter_range
        self.last_call_time = 0.0
        self.tokens = calls_per_minute
        self.last_refill = time.time()
        self._lock = threading.Lock()  # Thread-safety lock
    
    def wait_if_needed(self) -> float:
        """
        Wait if necessary to respect rate limits.
        Returns the actual wait time in seconds.
        Thread-safe implementation.
        """
        with self._lock:
            current_time = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = current_time - self.last_refill
            tokens_to_add = elapsed / self.min_interval
            self.tokens = min(self.calls_per_minute, self.tokens + tokens_to_add)
            self.last_refill = current_time
            
            # If we have tokens, use one
            if self.tokens >= 1:
                self.tokens -= 1
                wait_time = 0.0
            else:
                # Need to wait for a token
                wait_time = self.min_interval * random.uniform(*self.jitter_range)
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                self.tokens = 0
            
            self.last_call_time = time.time()
        
        # Sleep outside the lock to avoid blocking other threads
        if wait_time > 0:
            time.sleep(wait_time)
        
        return wait_time


# Global rate limiter instance
_rate_limiter = RateLimiter(calls_per_minute=AI_CONFIG.get('rate_limit', 15))


def get_gemini_client() -> genai.Client:
    """
    Factory function to get or create Gemini client.
    Validates API key at runtime and raises clear exception if missing.
    
    Returns:
        genai.Client: Configured Gemini client
        
    Raises:
        APIKeyError: If GOOGLE_API_KEY is not set or empty
    """
    global _gemini_client
    
    if _gemini_client is not None:
        return _gemini_client
    
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key or api_key.strip() == '':
        error_msg = (
            "GOOGLE_API_KEY environment variable is not set or empty. "
            "Please set it in your .env file or environment variables. "
            "Get your API key from: https://makersuite.google.com/app/apikey"
        )
        logger.error(error_msg)
        raise APIKeyError(error_msg)
    
    logger.info("Initializing Gemini client...")
    _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extract JSON from AI response text.
    Uses json.JSONDecoder().raw_decode() for reliable parsing.
    
    Args:
        text: Response text that may contain JSON
        
    Returns:
        Parsed JSON as dict, or None if extraction fails
    """
    if not text:
        return None
    
    # Try direct parsing first (best case: response is valid JSON)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try raw_decode to find JSON object in text
    decoder = json.JSONDecoder()
    
    # Find all potential JSON start positions
    for i, char in enumerate(text):
        if char == '{':
            try:
                obj, end = decoder.raw_decode(text, i)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    
    # Last resort: Try to find balanced braces (handles some edge cases)
    try:
        start = text.find('{')
        if start == -1:
            return None
        
        brace_count = 0
        end = start
        
        for i, char in enumerate(text[start:], start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break
        
        if end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    
    logger.warning("Failed to extract JSON from response")
    return None


class GeminiAnalyzer:
    """Wrapper for Gemini AI analysis functions with robust error handling."""
    
    def __init__(self):
        self.client = get_gemini_client()
        self.model_name = AI_CONFIG['model']
        
        # Remove 'models/' prefix if present for new SDK
        if self.model_name.startswith('models/'):
            self.model_name = self.model_name[7:]
        
        self.config = types.GenerateContentConfig(
            temperature=AI_CONFIG['temperature'],
            max_output_tokens=AI_CONFIG['max_tokens']
        )
    
    def _call_gemini(self, prompt: str, retry_count: int = 0) -> Optional[str]:
        """
        Call Gemini API with retry logic, rate limiting, and proper error handling.
        
        Args:
            prompt: The prompt to send to Gemini
            retry_count: Current retry attempt (for exponential backoff)
            
        Returns:
            Response text or None if all retries fail
        """
        max_retries = AI_CONFIG.get('retry_attempts', 3)
        
        # Proactive rate limiting with jitter
        _rate_limiter.wait_if_needed()
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.config
            )
            return response.text
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limit errors (429)
            if '429' in error_msg or 'quota' in error_msg or 'rate' in error_msg:
                if retry_count < max_retries:
                    # Exponential backoff with jitter
                    base_delay = 2 ** retry_count
                    jitter = random.uniform(0.5, 1.5)
                    delay = base_delay * jitter
                    logger.warning(f"Rate limited. Retrying in {delay:.1f}s (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(delay)
                    return self._call_gemini(prompt, retry_count + 1)
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} retries")
                    return None
            
            # Check for authentication errors
            elif 'auth' in error_msg or 'permission' in error_msg or 'invalid' in error_msg:
                logger.error(f"Authentication/Permission error: {e}")
                return None
            
            # Check for server errors (5xx)
            elif '500' in error_msg or '503' in error_msg or 'unavailable' in error_msg:
                if retry_count < max_retries:
                    delay = (2 ** retry_count) * random.uniform(0.5, 1.5)
                    logger.warning(f"Server error. Retrying in {delay:.1f}s")
                    time.sleep(delay)
                    return self._call_gemini(prompt, retry_count + 1)
                else:
                    logger.error(f"Server unavailable after {max_retries} retries: {e}")
                    return None
            
            # Generic retry for other errors
            else:
                if retry_count < max_retries:
                    delay = (2 ** retry_count) * random.uniform(0.5, 1.5)
                    logger.warning(f"API error: {e}. Retrying in {delay:.1f}s")
                    time.sleep(delay)
                    return self._call_gemini(prompt, retry_count + 1)
                else:
                    logger.error(f"Gemini API Error after {max_retries} retries: {e}")
                    return None


def calculate_consulting_fit_score(bid_data: Dict, firm_profile: Dict = FIRM_PROFILE) -> Dict:
    """
    Calculates Consulting Fit Score (CFS) for a bid.
    
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
        result = extract_json_from_response(response)
        if result and 'score' in result:
            return result
        else:
            logger.warning("Could not parse CFS response, using fallback")
            return {
                "score": 50,
                "verdict": "Marginal Fit",
                "reasoning": "Unable to analyze - insufficient information"
            }
    else:
        return {
            "score": 0,
            "verdict": "Analysis Failed",
            "reasoning": "Gemini API unavailable"
        }


def generate_go_no_go_matrix(bid_data: Dict, sow_text: str = "", firm_profile: Dict = FIRM_PROFILE) -> Dict:
    """
    Analyzes bid for Go/No-Go decision.
    
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
    
    # Calculate days to deadline with proper exception handling
    try:
        deadline = datetime.strptime(end_date, '%Y-%m-%d')
        today = datetime.now()
        days_left = (deadline - today).days
        timeline_flag = "RED" if days_left < 7 else "YELLOW" if days_left < 14 else "GREEN"
    except (ValueError, TypeError) as e:
        logger.debug(f"Could not parse end date '{end_date}': {e}")
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
        result = extract_json_from_response(response)
        if result:
            result['timeline_flag'] = timeline_flag  # Override with calculated value
            return result
    
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
    Generates executive summary of the bid.
    
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
        result = extract_json_from_response(response)
        if result:
            return result
    
    # Fallback
    return {
        "the_ask": f"Project related to {items}",
        "key_deliverables": ["To be determined from bid document"],
        "evaluation_criteria": "Not specified"
    }


def analyze_bid_complete(bid_data: Dict, sow_text: str = "", pdf_path: str = None) -> Dict:
    """
    Runs complete AI analysis on a bid.
    
    Args:
        bid_data: Bid information
        sow_text: Scope of Work text (optional, legacy)
        pdf_path: Path to local PDF file (for Virtual User)
    
    Returns:
        Complete analysis with CFS, Go/No-Go, and Summary
    """
    logger.info(f"Analyzing bid: {bid_data.get('Bid Number')}...")
    
    # Virtual User Step: If PDF exists, read it "manually"
    virtual_user_summary = ""
    if pdf_path and os.path.exists(pdf_path):
        from virtual_agent import BidReaderAgent
        logger.info(f"Virtual User: Reading document {os.path.basename(pdf_path)}...")
        try:
            agent = BidReaderAgent(pdf_path)
            virtual_user_summary = agent.summarize_sow()
            logger.info("Virtual User: SOW Summary generated.")
        except (FileNotFoundError, IOError, OSError) as e:
            logger.error(f"Virtual User file error: {e}")
            virtual_user_summary = f"Error reading document: {e}"
        except Exception as e:
            logger.error(f"Virtual User unexpected error: {e}")
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
        "sow_summary": final_sow_text,
        "analyzed_at": time.strftime('%Y-%m-%d %H:%M:%S')
    }


# =============================================================================
# A&D CONSULTING INTELLIGENCE INTEGRATION
# =============================================================================

def analyze_tender_ad_intelligence(bid_data: Dict, sow_text: str = "", pdf_path: str = None) -> Dict[str, Any]:
    """
    Comprehensive A&D Consulting Intelligence analysis.
    
    Combines:
    - Rule-based A&D domain scoring (6-component weighted algorithm)
    - Pattern detection for consulting vs goods classification
    - AI-powered executive summary and risk assessment
    
    Args:
        bid_data: Bid information dictionary
        sow_text: Scope of Work text (optional)
        pdf_path: Path to PDF for Virtual User extraction
        
    Returns:
        Complete A&D intelligence analysis with:
        - A&D relevance score (0-100)
        - Sub-category classification
        - Risk assessment
        - Recommendation (PURSUE/EVALUATE/PASS)
        - AI-generated insights
    """
    try:
        # Import A&D modules
        from ad_scorer import (
            analyze_tender_for_ad_consulting,
            generate_risk_assessment,
            generate_tender_summary
        )
        from pattern_detector import is_consulting_tender
        
        logger.info(f"Running A&D Intelligence analysis for: {bid_data.get('Bid Number')}")
        
        # Step 1: Extract SOW if PDF provided
        final_sow_text = sow_text
        if pdf_path and os.path.exists(pdf_path):
            from virtual_agent import BidReaderAgent
            try:
                agent = BidReaderAgent(pdf_path)
                final_sow_text = agent.summarize_sow()
                logger.info("SOW extracted by Virtual User")
            except Exception as e:
                logger.warning(f"Virtual User extraction failed: {e}")
        
        # Add SOW to tender data for analysis
        tender_data = dict(bid_data)
        tender_data['sow_text'] = final_sow_text
        
        # Step 2: Run A&D scoring algorithm
        ad_analysis = analyze_tender_for_ad_consulting(tender_data)
        
        # Step 3: Run pattern detection
        full_text = f"{bid_data.get('Items', '')} {bid_data.get('Department', '')} {final_sow_text}"
        is_consulting, consulting_prob, pattern_summary = is_consulting_tender(full_text)
        
        # Step 4: Generate risk assessment
        risk_assessment = generate_risk_assessment(tender_data, ad_analysis)
        
        # Step 5: Generate tender summary  
        tender_summary = generate_tender_summary(tender_data, ad_analysis)
        
        # Step 6: Run AI analysis for additional insights (using new trigger logic)
        ai_insights = None
        should_run_ai = ad_analysis.get('ai_trigger_status', False)
        trigger_reason = ad_analysis.get('ai_trigger_reason', 'Unknown')
        logger.info(f"AI Trigger Decision: {should_run_ai} - {trigger_reason}")
        
        if should_run_ai:
            cfs = calculate_consulting_fit_score(bid_data)
            ai_insights = {
                "cfs_score": cfs.get('score', 0),
                "cfs_verdict": cfs.get('verdict', 'N/A'),
                "cfs_reasoning": cfs.get('reasoning', '')
            }
        
        # Step 7: Run Intent-Driven Analysis (v4.1) for Partner Persona insights
        intent_analysis = None
        if should_run_ai:
            try:
                from intent_scorer import analyze_bid_intent
                intent_analysis = analyze_bid_intent(bid_data)
                logger.info(f"Intent Analysis: {intent_analysis.get('primary_archetype')} - {intent_analysis.get('priority_band')}")
            except ImportError as e:
                logger.warning(f"Intent scorer not available: {e}")
            except Exception as e:
                logger.error(f"Intent analysis failed: {e}")
        
        # Combine all results
        result = {
            "tender_id": bid_data.get('Bid Number', 'N/A'),
            "title": bid_data.get('Items', bid_data.get('title', 'N/A')),
            
            # A&D Intelligence Scores
            "is_consulting": round(consulting_prob, 2),
            "is_government_buyer": ad_analysis.get('is_government_buyer', True),
            "a_d_relevance_score": ad_analysis.get('a_d_relevance_score', 0),
            
            # Classifications
            "consulting_category": ad_analysis.get('consulting_category', 'Unknown'),
            "a_d_sub_category": ad_analysis.get('a_d_sub_category', 'Unknown'),
            
            # Confidence & Recommendation
            "confidence": ad_analysis.get('confidence', 50),
            "recommendation": ad_analysis.get('recommendation', 'EVALUATE'),
            
            # Detailed Analysis
            "matched_keywords": ad_analysis.get('matched_keywords', []),
            "matched_patterns": ad_analysis.get('matched_patterns', []) + pattern_summary,
            "score_components": ad_analysis.get('score_components', {}),
            
            # Summary & Risk
            "summary": tender_summary,
            "risk_assessment": risk_assessment,
            
            # AI Insights
            "ai_insights": ai_insights,
            
            # Reasoning
            "reasoning": ad_analysis.get('reasoning', ''),
            "interpretation": ad_analysis.get('interpretation', {}),
            
            # Metadata
            "sow_extracted": bool(final_sow_text),
            "analyzed_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            
            # Intent-Driven Analysis (v4.1)
            "intent_analysis": intent_analysis,
            "ai_trigger_reason": trigger_reason
        }
        
        logger.info(f"A&D Analysis complete: Score={result['a_d_relevance_score']}, Rec={result['recommendation']}")
        return result
        
    except ImportError as e:
        logger.error(f"A&D modules not available: {e}")
        # Fallback to standard analysis
        return analyze_bid_complete(bid_data, sow_text, pdf_path)
    except Exception as e:
        logger.error(f"A&D analysis failed: {e}")
        return {
            "error": str(e),
            "fallback_analysis": analyze_bid_complete(bid_data, sow_text, pdf_path)
        }

