"""
Intent-Driven Bid Intelligence Scorer (v4.1)

Implements the Partner Persona analysis with:
- P1-P12 Canonical Problem Archetypes
- Anti-Keyword guardrails
- Strict JSON output for dashboard integration

Author: Manoj Gundeti
Version: 4.1
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

from config import AI_CONFIG

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


# =============================================================================
# CANONICAL PROBLEM ARCHETYPES (v4.1)
# =============================================================================

PROBLEM_ARCHETYPES = {
    "P1": {
        "name": "Decision Defensibility Gap",
        "signals": ["feasibility", "dpr", "study", "assessment", "appraisal"],
        "risk": "Audit"
    },
    "P2": {
        "name": "Approval Conversion Failure",
        "signals": ["cabinet approval", "efc", "mou", "clearance", "sanction"],
        "risk": "Approval"
    },
    "P3": {
        "name": "Execution Slippage",
        "signals": ["pmu", "pmo", "implementation", "monitoring", "supervision"],
        "risk": "Execution"
    },
    "P4": {
        "name": "Governance & Accountability Ambiguity",
        "signals": ["governance", "accountability", "reform", "restructuring"],
        "risk": "Coordination"
    },
    "P5": {
        "name": "Policy / Regulatory Exposure",
        "signals": ["policy", "regulatory", "compliance", "statutory", "framework"],
        "risk": "Policy"
    },
    "P6": {
        "name": "Supply Chain Fragility",
        "signals": ["supply chain", "vendor", "procurement", "logistics", "indigenization"],
        "risk": "Execution"
    },
    "P7": {
        "name": "Institutional Capability Absence",
        "signals": ["capacity building", "training", "skill development", "capability"],
        "risk": "Execution"
    },
    "P8": {
        "name": "Fiscal & Commercial Bleed",
        "signals": ["cost optimization", "efficiency", "financial", "revenue", "commercial"],
        "risk": "Audit"
    },
    "P9": {
        "name": "Trapped Asset Value / Monetization",
        "signals": ["monetization", "asset", "disinvestment", "valuation", "restructuring"],
        "risk": "Approval"
    },
    "P10": {
        "name": "Citizen Service Fracture (UX / CX)",
        "signals": ["citizen", "service delivery", "grievance", "public service", "digital"],
        "risk": "Execution"
    },
    "P11": {
        "name": "Intelligence Void (M&E / Analytics)",
        "signals": ["m&e", "monitoring", "evaluation", "analytics", "dashboard", "mis"],
        "risk": "Audit"
    },
    "P12": {
        "name": "Pseudo-Consulting / Staff Augmentation Trap",
        "signals": ["man-month", "manpower", "resource", "deployment", "on-site", "staff"],
        "risk": "Execution",
        "is_negative": True
    }
}


# =============================================================================
# SYSTEM PROMPT (v4.1) - Partner Persona
# =============================================================================

SYSTEM_PROMPT = """You are a Senior Public Sector Consulting Partner with 20+ years of experience.

You think in terms of:
- Audit defensibility
- Approval risk
- Execution failure
- Commercial sanity

You do NOT think in keywords or categories. Bids describe PROBLEMS, RISKS, and OBLIGATIONS.

CORE RULES:
1. NEVER classify services directly
2. ALWAYS identify the underlying problem first
3. Use ONLY canonical problem archetypes P1-P12
4. Explain reasoning in cause → risk → control logic
5. Keywords alone are NEVER sufficient
6. If reasoning is weak or ambiguous → reduce confidence
7. Escalate when defined conditions are met

CANONICAL PROBLEM ARCHETYPES:
P1 — Decision Defensibility Gap
P2 — Approval Conversion Failure
P3 — Execution Slippage
P4 — Governance & Accountability Ambiguity
P5 — Policy / Regulatory Exposure
P6 — Supply Chain Fragility
P7 — Institutional Capability Absence
P8 — Fiscal & Commercial Bleed
P9 — Trapped Asset Value / Monetization
P10 — Citizen Service Fracture (UX / CX)
P11 — Intelligence Void (M&E / Analytics)
P12 — Pseudo-Consulting / Staff Augmentation Trap (NEGATIVE - always flag)

INTENT MODE:
- SINGLE → one dominant lifecycle problem
- COMPOSITE → multiple lifecycle stages (≥3 archetypes AND ≥2 lifecycle stages)
  If COMPOSITE, flag as "Account Expansion Opportunity"

ANTI-KEYWORD GUARDRAIL:
If you cite a keyword, you MUST explain why it indicates a deeper failure mode.
If you cannot → reduce confidence.

OUTPUT FORMAT (STRICT JSON ONLY - NO MARKDOWN):
{
  "platform": "gem|cppp|defence",
  "bid_id": "string",
  "buyer_intent": "one sentence summary",
  "intent_mode": "SINGLE|COMPOSITE",
  "primary_archetype": "P1-P12",
  "secondary_archetypes": ["P2", "P5"],
  "dominant_risk": "Approval|Audit|Execution|Policy|Coordination",
  "primary_service": "string",
  "secondary_services": ["string"],
  "commercial_risk": false,
  "reasoning": [
    "signal → problem",
    "risk implication",
    "service/control justification"
  ],
  "confidence_scores": {
    "problem_clarity": 0-5,
    "governance_pressure": 0-5,
    "lifecycle_certainty": 0-5,
    "deliverable_fit": 0-5,
    "capability_depth": 0-5,
    "final_percent": 0-100
  },
  "escalate_to_human": false,
  "priority_band": "HIGH|MEDIUM|LOW",
  "action": "Pursue|Review|Reject"
}

PRIORITY BANDS:
- HIGH (≥80% confidence) → Pursue now
- MEDIUM (60-79%) → Review
- LOW (<60%) → Monitor/Reject

Provide ONLY the JSON. No markdown. No commentary. No extra text."""


# =============================================================================
# RUN PROMPT TEMPLATE (v4.1)
# =============================================================================

RUN_PROMPT_TEMPLATE = """Analyze this bid from {platform} portal:

**Bid ID:** {bid_id}
**Title/Category:** {title}
**Department/Buyer:** {department}
**Description/Items:** {items}
**Budget:** {budget}
**End Date:** {end_date}

PRE-FILTER RULES:
- Discard ONLY IF ≥80% scope is physical execution AND no advisory/PMO component
- Do NOT discard civil/construction projects automatically (PMC/PMO on civil works is valid)

ANALYSIS STEPS:
1. BUYER INTENT: What decision is the buyer trying to defend? What fails if they get it wrong?
2. DOMINANT RISK: Select ONE (Approval|Audit|Execution|Policy|Coordination)
3. ARCHETYPE MAPPING: Map to P1-P12 (1 primary, 0-2 secondary). CHECK P12 explicitly.
4. SERVICE MAPPING: Use archetype truth table. Do not invent services.
5. CONFIDENCE SCORING: Score each dimension 0-5 and normalize to final_percent.
6. ESCALATION: Always escalate if P12 detected, restricted buyer, or Strategy+PMO conflict.

Respond with ONLY valid JSON as specified in the system prompt."""


class IntentDrivenScorer:
    """
    Intent-Driven Bid Intelligence Scorer (v4.1)
    
    Implements the Partner Persona analysis with strict JSON output.
    """
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = AI_CONFIG.get('model', 'gemini-2.0-flash')
        
        # Remove 'models/' prefix if present
        if self.model_name.startswith('models/'):
            self.model_name = self.model_name[7:]
        
        self.config = types.GenerateContentConfig(
            temperature=0.3,  # Lower temperature for consistent JSON output
            max_output_tokens=2048
        )
    
    def analyze_bid(self, bid_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a bid using the Intent-Driven v4.1 logic.
        
        Args:
            bid_data: Dictionary with bid information
            
        Returns:
            Structured analysis dictionary with archetype mapping, risk, and recommendation
        """
        # Extract bid details
        bid_id = bid_data.get('Bid Number', bid_data.get('bid_id', 'N/A'))
        title = bid_data.get('Items', bid_data.get('title', 'N/A'))
        department = bid_data.get('Department', bid_data.get('department', 'N/A'))
        items = bid_data.get('Items', bid_data.get('description', ''))
        budget = bid_data.get('Budget', bid_data.get('budget', 'Not specified'))
        end_date = bid_data.get('End Date', bid_data.get('end_date', 'N/A'))
        platform = bid_data.get('Source Portal', bid_data.get('source_portal', 'gem'))
        
        # Prepare the run prompt
        run_prompt = RUN_PROMPT_TEMPLATE.format(
            platform=platform,
            bid_id=bid_id,
            title=title,
            department=department,
            items=items,
            budget=budget,
            end_date=end_date
        )
        
        try:
            # Call Gemini with system prompt
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
                    {"role": "model", "parts": [{"text": "Understood. I will analyze bids as a Senior Public Sector Consulting Partner, using the P1-P12 archetype framework and outputting strict JSON only."}]},
                    {"role": "user", "parts": [{"text": run_prompt}]}
                ],
                config=self.config
            )
            
            # Parse JSON response
            result = self._extract_json(response.text)
            
            if result:
                # Add metadata
                result['bid_id'] = bid_id
                result['platform'] = platform
                result['analyzed_with'] = 'intent_scorer_v4.1'
                
                # Flag P12 (Staff Augmentation Trap)
                if result.get('primary_archetype') == 'P12':
                    result['commercial_risk'] = True
                    result['priority_band'] = 'MEDIUM' if result.get('priority_band') == 'HIGH' else result.get('priority_band')
                    result['escalate_to_human'] = True
                    logger.warning(f"P12 (Staff Aug) detected for {bid_id} - flagged for human review")
                
                return result
            else:
                logger.error(f"Failed to parse JSON response for {bid_id}")
                return self._fallback_analysis(bid_data)
                
        except Exception as e:
            logger.error(f"Intent analysis failed for {bid_id}: {e}")
            return self._fallback_analysis(bid_data)
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from response text, handling various AI response formats.
        
        Handles:
        - Direct JSON
        - Markdown code blocks (```json ... ```)
        - JSON with surrounding text
        - Nested braces
        """
        if not text:
            return None
        
        text = text.strip()
        
        # Method 1: Try direct parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract from markdown code block ```json ... ```
        import re
        json_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Method 3: Find JSON object using brace matching
        try:
            start = text.find('{')
            if start == -1:
                return None
            
            brace_count = 0
            end = start
            in_string = False
            escape_next = False
            
            for i, char in enumerate(text[start:], start):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                    
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            if end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON decode error: {e}")
            pass
        
        # Method 4: Try to fix common JSON issues
        try:
            # Remove trailing commas before } or ]
            fixed_text = re.sub(r',\s*([}\]])', r'\1', text)
            start = fixed_text.find('{')
            end = fixed_text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(fixed_text[start:end])
        except json.JSONDecodeError:
            pass
        
        return None

    
    def _fallback_analysis(self, bid_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback analysis when AI fails."""
        bid_id = bid_data.get('Bid Number', bid_data.get('bid_id', 'N/A'))
        
        return {
            "bid_id": bid_id,
            "platform": bid_data.get('Source Portal', 'gem'),
            "buyer_intent": "Unable to analyze - fallback mode",
            "intent_mode": "SINGLE",
            "primary_archetype": "P3",
            "secondary_archetypes": [],
            "dominant_risk": "Execution",
            "primary_service": "PMU/Implementation Support",
            "secondary_services": [],
            "commercial_risk": False,
            "reasoning": ["Fallback analysis - AI unavailable"],
            "confidence_scores": {
                "problem_clarity": 0,
                "governance_pressure": 0,
                "lifecycle_certainty": 0,
                "deliverable_fit": 0,
                "capability_depth": 0,
                "final_percent": 0
            },
            "escalate_to_human": True,
            "priority_band": "LOW",
            "action": "Review",
            "analyzed_with": "intent_scorer_v4.1_fallback"
        }
    
    def quick_prefilter(self, bid_data: Dict[str, Any]) -> bool:
        """
        Quick pre-filter to check if bid should be analyzed.
        
        STRICT MODE: Only passes bids that show clear signals of consulting/advisory work.
        Returns True if bid should be analyzed, False if it should be skipped.
        """
        title = bid_data.get('Items', bid_data.get('title', '')).lower()
        description = bid_data.get('description', '').lower()
        department = bid_data.get('Department', '').lower()
        full_text = f"{title} {description} {department}"
        
        # ========== HARD EXCLUSIONS - Always filter out ==========
        hard_exclude_signals = [
            # Equipment and hardware procurement
            'supply of', 'procurement of', 'purchase of', 'buying',
            'hardware supply', 'equipment supply', 'material supply',
            'dg set', 'generator', 'ups ', 'air conditioner', 'ac unit', 'hvac',
            'display', 'monitor', 'printer', 'copier', 'scanner', 'laptop', 'desktop',
            'grinding machine', 'tool machine', 'lathe', 'milling', 'cnc',
            'server rack', 'network switch', 'router', 'firewall hardware',
            'spare parts', 'components', 'accessories',
            
            # Furniture and fixtures
            'desk and chair', 'desk and bench', 'furniture', 'locker',
            'writing board', 'whiteboard', 'dry erase', 'table and chair',
            'steel almirah', 'steel cupboard', 'shelf', 'shelving', 'cabinet',
            
            # Consumables and supplies 
            'copier paper', 'stationery', 'toner', 'cartridge', 'ink ',
            'plain paper', 'a4 paper', 'envelope', 'file cover', 'binding',
            'books and', 'reference material', 'publication',
            
            # Software licenses (not consulting) 
            'windows 11', 'windows server', 'windows 10', 'microsoft office',
            'operating system', 'antivirus', 'license renewal', 'subscription',
            'software license', 'oracle license', 'sap license',
            
            # Maintenance and services (not consulting)
            'annual maintenance', 'amc ', 'repair and maintenance', 'servicing',
            'housekeeping', 'security guard', 'catering', 'canteen', 'mess ',
            'de-ratting', 'de-cockroach', 'pest control', 'cleaning service',
            'cab hiring', 'taxi hiring', 'vehicle hiring', 'transportation',
            'demilitarization', 'demolition', 'disposal', 'scrap',
            'laundry', 'washing', 'sanitation',
            
            # Construction and civil works (without PMC/advisory)
            'construction of building', 'civil construction', 'building work',
            'road construction', 'flooring', 'painting work', 'interior work',
            'plumbing', 'electrical wiring', 'renovation work', 'repair work',
            'masonry', 'carpentry', 'fabrication',
            
            # Uniforms, clothing, textiles
            'uniform', 'clothing', 'textile', 'fabric', 'garment', 'footwear',
            
            # Medical supplies (not consulting)
            'surgical', 'medicine', 'pharmaceutical', 'drug supply', 'tablet',
            'lab equipment', 'x-ray', 'mri', 'ct scan', 'medical equipment',
            'hospital bed', 'wheelchair', 'syringe', 'bandage', 'gloves',
            
            # Food and provisions
            'ration', 'food items', 'grocery', 'provisions', 'dal ', 'rice ',
            'vegetables', 'fruits', 'meat', 'poultry',
            
            # Training equipment (not training consulting)
            'training module', 'training equipment', 'training machine',
            'simulator', 'physical training', 'gym equipment',
            
            # Audio/video equipment
            'audio system', 'reinforcement system', 'sound system',
            'video conferencing equipment', 'projector', 'screen ',
            'microphone', 'speaker', 'amplifier',
            
            # Ammunition and explosives
            'ammunition', 'explosive', 'ordnance', 'munition', 'arms ',
            
            # Vehicles and transport
            'vehicle procurement', 'bus ', 'car ', 'truck ', 'jeep ',
            'motorcycle', 'scooter', 'ambulance',
            
            # Chemicals and industrial
            'chemical', 'lubricant', 'oil ', 'grease', 'fuel ',
            
            # IT Hardware
            'keyboard', 'mouse', 'cable', 'wire', 'connector', 'adapter',
        ]
        
        # ========== POSITIVE CONSULTING SIGNALS - Required to pass ==========
        consulting_signals = [
            # Direct consulting terms
            'consultant', 'consulting', 'consultancy', 
            'advisory', 'advisor', 'advising',
            
            # Project management consulting
            'pmu', 'pmo', 'project management unit', 'project management consultant',
            'programme management', 'project monitoring',
            
            # Evaluation and assessment
            'monitoring', 'evaluation', 'm&e', 'impact assessment',
            'baseline study', 'endline study', 'mid-term review',
            
            # Research and studies
            'study', 'survey', 'research', 'analysis',
            'assessment', 'appraisal', 'audit', 'review',
            
            # Strategy and planning
            'strategy', 'strategic', 'planning', 'roadmap',
            'master plan', 'action plan', 'blueprint',
            
            # DPR and feasibility
            'dpr', 'feasibility', 'detailed project report',
            'pre-feasibility', 'techno-economic',
            
            # Capacity building (consulting)
            'capacity building', 'training programme', 'training of trainers',
            'institutional strengthening', 'skill development',
            
            # Policy and governance
            'policy', 'reform', 'governance', 'regulatory',
            'framework development', 'guideline',
            
            # Digital and IT consulting
            'digital transformation', 'it consulting', 'erp implementation',
            'e-governance', 'system integration', 'digital india',
            'software development', 'application development', 'portal development',
            
            # Knowledge and documentation
            'knowledge management', 'documentation', 'manual preparation',
            'process re-engineering', 'business process',
            
            # Design consultancy
            'design consultant', 'architectural consultant', 'engineering consultant',
            
            # Third party
            'third party', 'tpia', 'tpa ', 'quality assurance consultant',
            
            # Agency/empanelment
            'empanelment', 'agency for', 'hiring of agency',
            'engagement of', 'selection of consultant',
        ]
        
        # Check for hard exclusions
        has_hard_exclusion = any(s in full_text for s in hard_exclude_signals)
        
        # Check for positive consulting signals
        has_consulting_signal = any(s in full_text for s in consulting_signals)
        
        # STRICT LOGIC:
        # 1. If has hard exclusion AND no consulting signal → REJECT
        # 2. If has consulting signal → PASS (even with some exclusion terms, the consulting intent is clear)
        # 3. If neither → REJECT (no clear consulting intent)
        
        if has_consulting_signal:
            return True
        
        if has_hard_exclusion:
            logger.debug(f"Pre-filter: Skipping {bid_data.get('Bid Number', 'N/A')} - procurement/supply bid")
            return False
        
        # No consulting signal and no exclusion - still reject as it's likely generic procurement
        logger.debug(f"Pre-filter: Skipping {bid_data.get('Bid Number', 'N/A')} - no consulting signals detected")
        return False



def analyze_bid_intent(bid_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze a bid with Intent-Driven v4.1 logic.
    
    Args:
        bid_data: Bid information dictionary
        
    Returns:
        Analysis result dictionary
    """
    scorer = IntentDrivenScorer()
    
    # Pre-filter
    if not scorer.quick_prefilter(bid_data):
        return {
            "bid_id": bid_data.get('Bid Number', 'N/A'),
            "platform": bid_data.get('Source Portal', 'gem'),
            "buyer_intent": "Pre-filtered: Physical execution scope",
            "intent_mode": "SINGLE",
            "primary_archetype": "P12",
            "secondary_archetypes": [],
            "dominant_risk": "Execution",
            "primary_service": "N/A",
            "secondary_services": [],
            "commercial_risk": True,
            "reasoning": ["Pre-filtered as physical execution with no advisory component"],
            "confidence_scores": {
                "problem_clarity": 0,
                "governance_pressure": 0,
                "lifecycle_certainty": 0,
                "deliverable_fit": 0,
                "capability_depth": 0,
                "final_percent": 0
            },
            "escalate_to_human": False,
            "priority_band": "LOW",
            "action": "Reject",
            "analyzed_with": "intent_scorer_v4.1_prefilter"
        }
    
    return scorer.analyze_bid(bid_data)
