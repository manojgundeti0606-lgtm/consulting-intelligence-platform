"""
A&D Consulting Intelligence - Scoring Engine
Implements the 6-component weighted A&D relevance scoring algorithm

Author: Manoj Gundeti
Last Updated: 2025-12-26
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

from ad_taxonomy import (
    GPS_IDENTIFIERS, CONSULTING_KEYWORDS, AD_KEYWORDS, SEMANTIC_EXPANSION,
    NEGATIVE_KEYWORDS, AD_BUYER_TIERS, AD_SUBCATEGORIES, CONSULTING_CATEGORIES,
    get_all_consulting_keywords, get_all_ad_keywords, get_all_negative_keywords,
    get_buyer_tier, classify_ad_subcategory, classify_consulting_category
)
from ad_config import (
    SCORING_WEIGHTS, KEYWORD_SCORING, STRUCTURAL_SCORING,
    get_budget_score, get_duration_score, get_recommendation,
    get_score_interpretation, get_capability_score
)

# Configure logging
logger = logging.getLogger(__name__)


class ADScorer:
    """
    A&D Consulting Intelligence Scoring Engine
    
    Implements:
    A&D_RELEVANCE_SCORE = 
        (KEYWORD_MATCH × 0.35) +
        (STRUCTURAL_FIT × 0.25) +
        (BUDGET_ALIGNMENT × 0.15) +
        (DURATION_ALIGNMENT × 0.10) +
        (BUYER_ALIGNMENT × 0.10) +
        (CAPABILITY_GAP × 0.05)
    """
    
    def __init__(self):
        self.consulting_keywords = get_all_consulting_keywords()
        self.ad_keywords = get_all_ad_keywords()
        self.negative_keywords = get_all_negative_keywords()
    
    def calculate_ad_relevance_score(self, tender_data: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive A&D relevance score for a tender.
        
        Args:
            tender_data: Dictionary containing tender information
                - title: Tender title
                - description: Tender description
                - items: Items/category
                - department/buyer: Buyer organization
                - budget: Budget in INR
                - duration: Duration in months (or end_date)
                - sow_text: Scope of Work text (optional)
        
        Returns:
            Complete analysis dictionary with scores, classifications, and recommendations
        """
        # Extract text content
        title = tender_data.get('title', tender_data.get('Bid Number', ''))
        description = tender_data.get('description', tender_data.get('Items', ''))
        buyer = tender_data.get('department', tender_data.get('Department', ''))
        sow_text = tender_data.get('sow_text', '')
        
        # Combine all text for analysis
        full_text = f"{title} {description} {buyer} {sow_text}".lower()
        
        # Calculate component scores
        keyword_score, matched_keywords = self._calculate_keyword_score(full_text)
        structural_score, matched_patterns = self._calculate_structural_score(tender_data, full_text)
        budget_score = self._calculate_budget_score(tender_data)
        duration_score = self._calculate_duration_score(tender_data)
        buyer_score = self._calculate_buyer_score(buyer)
        capability_score = get_capability_score(full_text)
        
        # Calculate weighted overall score
        ad_relevance_score = (
            keyword_score * SCORING_WEIGHTS["keyword_match"] +
            structural_score * SCORING_WEIGHTS["structural_fit"] +
            budget_score * SCORING_WEIGHTS["budget_alignment"] +
            duration_score * SCORING_WEIGHTS["duration_alignment"] +
            buyer_score * SCORING_WEIGHTS["buyer_alignment"] +
            capability_score * SCORING_WEIGHTS["capability_gap"]
        )
        
        # Calculate consulting confidence
        is_consulting = self._calculate_consulting_confidence(full_text, matched_patterns)
        
        # Determine if government buyer
        is_government_buyer = self._is_government_buyer(buyer, full_text)
        
        # Classify categories
        consulting_category = classify_consulting_category(full_text)
        ad_subcat_id, ad_subcategory = classify_ad_subcategory(full_text, matched_keywords)
        
        # Get recommendation
        budget = self._extract_budget(tender_data)
        recommendation = get_recommendation(ad_relevance_score, is_consulting, budget)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            keyword_score, structural_score, is_consulting, len(matched_keywords)
        )
        
        # Get score interpretation
        interpretation = get_score_interpretation(ad_relevance_score)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            matched_keywords, matched_patterns, buyer, 
            ad_relevance_score, recommendation, tender_data
        )
        
        return {
            "tender_id": tender_data.get('Bid Number', tender_data.get('tender_id', 'N/A')),
            "title": title,
            "is_consulting": round(is_consulting, 2),
            "is_government_buyer": is_government_buyer,
            "a_d_relevance_score": round(ad_relevance_score, 1),
            "consulting_category": consulting_category,
            "a_d_sub_category": ad_subcategory,
            "confidence": round(confidence, 1),
            "matched_keywords": matched_keywords[:20],  # Limit to top 20
            "matched_patterns": matched_patterns,
            "recommendation": recommendation,
            "score_components": {
                "keyword_match": round(keyword_score, 1),
                "structural_fit": round(structural_score, 1),
                "budget_alignment": round(budget_score, 1),
                "duration_alignment": round(duration_score, 1),
                "buyer_alignment": round(buyer_score, 1),
                "capability_gap": round(capability_score, 1)
            },
            "interpretation": interpretation,
            "reasoning": reasoning
        }
    
    def _calculate_keyword_score(self, text: str) -> Tuple[float, List[str]]:
        """Calculate keyword match score"""
        score = 0
        matched = []
        
        # Check GPS identifiers (Layer 1)
        gps_found = False
        for kw in GPS_IDENTIFIERS["strong"]["keywords"]:
            if kw.lower() in text:
                gps_found = True
                matched.append(f"GPS:{kw}")
                break
        
        if not gps_found:
            for kw in GPS_IDENTIFIERS["medium"]["keywords"]:
                if kw.lower() in text:
                    gps_found = True
                    matched.append(f"GPS:{kw}")
                    break
        
        # Check A&D keywords (Layer 3)
        ad_found = False
        for category, keywords in AD_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    ad_found = True
                    matched.append(f"A&D:{kw}")
        
        # GPS + A&D present
        if gps_found and ad_found:
            score += KEYWORD_SCORING["gps_ad_present"]  # +40
        
        # Check consulting keywords (Layer 2)
        consulting_found = False
        for category, keywords in CONSULTING_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    consulting_found = True
                    matched.append(f"Consulting:{kw}")
        
        # Semantic expansion keywords in consulting context (Layer 4)
        if consulting_found:
            for category, keywords in SEMANTIC_EXPANSION.items():
                for kw in keywords:
                    if kw.lower() in text:
                        score += 2  # Small bonus for each semantic match
                        matched.append(f"Semantic:{kw}")
            score = min(score + KEYWORD_SCORING["semantic_consulting"], 
                       KEYWORD_SCORING["max_score"])
        
        # A&D modifiers
        ad_modifiers = ["procurement", "strategy", "modernization", "advisory", "consulting"]
        for mod in ad_modifiers:
            if mod in text and ad_found:
                score += 4
                matched.append(f"Modifier:{mod}")
        
        score = min(score, KEYWORD_SCORING["max_score"])
        
        # Check negative keywords (Layer 5) - penalties
        for neg_kw in NEGATIVE_KEYWORDS["hard_exclusions"]:
            if neg_kw.lower() in text:
                score += KEYWORD_SCORING["exclusion_penalty"]  # -20
                matched.append(f"EXCLUDE:{neg_kw}")
                break  # Only penalize once
        
        # Ensure score is within bounds
        score = max(0, min(score, KEYWORD_SCORING["max_score"]))
        
        return score, list(set(matched))  # Remove duplicates
    
    def _calculate_structural_score(self, tender_data: Dict, text: str) -> Tuple[float, List[str]]:
        """Calculate structural fit score based on tender structure"""
        score = 0
        patterns = []
        
        # Pattern 1: Multi-factor evaluation criteria
        eval_patterns = [
            r"experience.*?\d+%",
            r"technical.*?\d+%",
            r"approach.*?\d+%",
            r"team.*?\d+%",
            r"price.*?\d+%",
            r"qcbs",
            r"quality.*cost.*based"
        ]
        for pattern in eval_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += STRUCTURAL_SCORING["evaluation_criteria"]
                patterns.append("Multi-factor evaluation criteria detected")
                break
        
        # Pattern 2: Detailed SOW with phases
        sow_patterns = [
            r"phase\s*\d",
            r"deliverable",
            r"milestone",
            r"output",
            r"scope of work",
            r"person.?months?",
            r"person.?days?"
        ]
        sow_count = sum(1 for p in sow_patterns if re.search(p, text, re.IGNORECASE))
        if sow_count >= 2:
            score += STRUCTURAL_SCORING["detailed_sow"]
            patterns.append(f"Detailed SOW detected ({sow_count} indicators)")
        
        # Pattern 3: Team credentials required
        team_patterns = [
            r"cv.*required",
            r"resume",
            r"team\s*composition",
            r"key\s*personnel",
            r"expert.*profile",
            r"qualification.*team"
        ]
        for pattern in team_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += STRUCTURAL_SCORING["team_credentials"]
                patterns.append("Team credentials/CVs required")
                break
        
        # Pattern 4: Duration threshold (≥6 months)
        duration = self._extract_duration(tender_data)
        if duration and duration >= 6:
            score += STRUCTURAL_SCORING["duration_threshold"]
            patterns.append(f"Duration {duration} months (≥6 months)")
        
        # Pattern 5: Budget threshold (≥₹1 Crore)
        budget = self._extract_budget(tender_data)
        if budget >= 10000000:  # ₹1 Crore
            score += STRUCTURAL_SCORING["budget_threshold"]
            patterns.append(f"Budget ₹{budget/10000000:.1f} Cr (≥₹1 Cr)")
        
        score = min(score, STRUCTURAL_SCORING["max_score"])
        return score, patterns
    
    def _calculate_budget_score(self, tender_data: Dict) -> float:
        """Calculate budget alignment score"""
        budget = self._extract_budget(tender_data)
        return get_budget_score(budget)
    
    def _calculate_duration_score(self, tender_data: Dict) -> float:
        """Calculate duration alignment score"""
        duration = self._extract_duration(tender_data)
        if duration:
            return get_duration_score(duration)
        return 50  # Default moderate score if unknown
    
    def _calculate_buyer_score(self, buyer: str) -> float:
        """Calculate buyer alignment score"""
        tier, score = get_buyer_tier(buyer)
        return score
    
    def _calculate_consulting_confidence(self, text: str, patterns: List[str]) -> float:
        """Calculate confidence that this is a consulting tender"""
        confidence = 0.5  # Start neutral
        
        # Check consulting keywords
        consulting_count = sum(1 for kw in self.consulting_keywords if kw in text)
        confidence += min(consulting_count * 0.05, 0.25)  # Up to +25%
        
        # Check structural patterns
        if patterns:
            confidence += min(len(patterns) * 0.08, 0.20)  # Up to +20%
        
        # Check for negative keywords (goods procurement)
        for neg in NEGATIVE_KEYWORDS["hard_exclusions"]:
            if neg.lower() in text:
                confidence -= 0.15
                break
        
        # Boost for specific consulting phrases
        consulting_phrases = [
            "consulting services", "advisory services", "professional services",
            "strategic planning", "feasibility study", "detailed project report"
        ]
        for phrase in consulting_phrases:
            if phrase in text:
                confidence += 0.10
                break
        
        return max(0, min(confidence, 1.0))
    
    def _is_government_buyer(self, buyer: str, text: str) -> bool:
        """Determine if the buyer is a government entity"""
        buyer_lower = buyer.lower()
        
        # Check all GPS identifiers
        for category in GPS_IDENTIFIERS.values():
            for kw in category["keywords"]:
                if kw.lower() in buyer_lower or kw.lower() in text:
                    return True
        
        return False
    
    def _extract_budget(self, tender_data: Dict) -> float:
        """Extract budget amount from tender data"""
        budget = tender_data.get('budget', tender_data.get('Budget', 0))
        
        if isinstance(budget, (int, float)):
            return float(budget)
        
        if isinstance(budget, str):
            # Try to parse budget string
            budget = budget.replace(',', '').replace('₹', '').replace('Rs', '').strip()
            
            # Handle Crore/Lakh notation
            if 'cr' in budget.lower():
                match = re.search(r'([\d.]+)', budget)
                if match:
                    return float(match.group(1)) * 10000000
            elif 'lakh' in budget.lower() or 'lac' in budget.lower():
                match = re.search(r'([\d.]+)', budget)
                if match:
                    return float(match.group(1)) * 100000
            else:
                try:
                    return float(budget)
                except:
                    pass
        
        return 0
    
    def _extract_duration(self, tender_data: Dict) -> Optional[int]:
        """Extract duration in months from tender data"""
        duration = tender_data.get('duration', tender_data.get('Duration'))
        
        if duration:
            if isinstance(duration, (int, float)):
                return int(duration)
            if isinstance(duration, str):
                match = re.search(r'(\d+)', duration)
                if match:
                    return int(match.group(1))
        
        # Try to calculate from dates
        end_date = tender_data.get('End Date', tender_data.get('end_date'))
        if end_date:
            try:
                if isinstance(end_date, str):
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end = end_date
                today = datetime.now()
                months = (end.year - today.year) * 12 + (end.month - today.month)
                return max(0, months)
            except:
                pass
        
        return None
    
    def _calculate_confidence(self, keyword_score: float, structural_score: float, 
                             is_consulting: float, keyword_count: int) -> float:
        """Calculate overall confidence in the classification"""
        confidence = 50  # Start at 50%
        
        # Adjust based on keyword score
        if keyword_score >= 70:
            confidence += 20
        elif keyword_score >= 50:
            confidence += 10
        
        # Adjust based on structural score
        if structural_score >= 70:
            confidence += 15
        elif structural_score >= 50:
            confidence += 8
        
        # Adjust based on consulting confidence
        confidence += (is_consulting - 0.5) * 30  # -15 to +15
        
        # Adjust based on keyword count
        if keyword_count >= 10:
            confidence += 10
        elif keyword_count >= 5:
            confidence += 5
        
        return max(0, min(confidence, 100))
    
    def _generate_reasoning(self, keywords: List[str], patterns: List[str], 
                           buyer: str, score: float, recommendation: str,
                           tender_data: Dict) -> str:
        """Generate human-readable reasoning for the score and recommendation"""
        parts = []
        
        # Keyword summary
        ad_keywords = [k for k in keywords if k.startswith("A&D:")]
        consulting_keywords = [k for k in keywords if k.startswith("Consulting:")]
        
        if ad_keywords:
            parts.append(f"A&D keywords detected: {', '.join([k.split(':')[1] for k in ad_keywords[:5]])}")
        
        if consulting_keywords:
            parts.append(f"Consulting indicators: {', '.join([k.split(':')[1] for k in consulting_keywords[:5]])}")
        
        # Buyer analysis
        tier, tier_score = get_buyer_tier(buyer)
        parts.append(f"Buyer: {buyer} ({tier}, score: {tier_score})")
        
        # Pattern summary
        if patterns:
            parts.append(f"Structural patterns: {'; '.join(patterns[:3])}")
        
        # Score interpretation
        interpretation = get_score_interpretation(score)
        parts.append(f"Classification: {interpretation['label']} - {interpretation['description']}")
        
        # Recommendation rationale
        if recommendation == "PURSUE":
            parts.append("High A&D consulting fit. Recommend active pursuit with dedicated team.")
        elif recommendation == "EVALUATE":
            parts.append("Mixed signals or moderate fit. Recommend further evaluation of SOW and requirements.")
        else:
            parts.append("Low fit or likely not consulting. Recommend passing unless specific interest.")
        
        return " | ".join(parts)


def analyze_tender_for_ad_consulting(tender_data: Dict) -> Dict[str, Any]:
    """
    Convenience function to analyze a tender for A&D consulting fit.
    
    Args:
        tender_data: Tender information dictionary
        
    Returns:
        Complete analysis dictionary
    """
    scorer = ADScorer()
    return scorer.calculate_ad_relevance_score(tender_data)


def generate_risk_assessment(tender_data: Dict, ad_analysis: Dict) -> Dict[str, str]:
    """
    Generate risk assessment for a tender.
    
    Returns:
        Dictionary with risk levels for each category
    """
    # Simple heuristic-based risk assessment
    score = ad_analysis.get("a_d_relevance_score", 50)
    confidence = ad_analysis.get("confidence", 50)
    patterns = ad_analysis.get("matched_patterns", [])
    
    # Implementation risk
    if "Detailed SOW detected" in str(patterns) and confidence >= 70:
        implementation_risk = "Low"
    elif confidence >= 50:
        implementation_risk = "Medium"
    else:
        implementation_risk = "High"
    
    # Scope creep risk
    sow_mentioned = any("SOW" in p or "scope" in p.lower() for p in patterns)
    if sow_mentioned and len(patterns) >= 3:
        scope_creep_risk = "Low"
    elif len(patterns) >= 2:
        scope_creep_risk = "Medium"
    else:
        scope_creep_risk = "High"
    
    # Political risk (based on buyer tier)
    buyer_tier, _ = get_buyer_tier(tender_data.get('Department', ''))
    if buyer_tier in ["tier_1", "tier_2"]:
        political_risk = "Low"
    elif buyer_tier in ["tier_3", "tier_4"]:
        political_risk = "Medium"
    else:
        political_risk = "Medium"
    
    # Win probability
    if score >= 80 and confidence >= 70:
        win_probability = "High"
    elif score >= 60 and confidence >= 50:
        win_probability = "Medium"
    else:
        win_probability = "Low"
    
    return {
        "implementation_risk": implementation_risk,
        "scope_creep_risk": scope_creep_risk,
        "political_risk": political_risk,
        "win_probability": win_probability
    }


def generate_tender_summary(tender_data: Dict, ad_analysis: Dict) -> Dict[str, Any]:
    """
    Generate structured summary of the tender.
    
    Returns:
        Summary dictionary with key fields
    """
    return {
        "buyer": tender_data.get('Department', tender_data.get('department', 'Unknown')),
        "scope": tender_data.get('Items', tender_data.get('description', 'See tender document')),
        "budget": f"₹{ad_analysis.get('score_components', {}).get('budget_alignment', 0)/10:.1f} Cr (estimated)",
        "duration": f"{tender_data.get('duration', 'TBD')} months",
        "key_deliverables": ["As per tender document - requires SOW extraction"],
        "required_qualifications": ["Government consulting experience", "Domain expertise"]
    }
