"""
A&D Consulting Intelligence - Pattern Detection Engine
Detects structural patterns to differentiate consulting from goods procurement

Author: Manoj Gundeti
Last Updated: 2025-12-26
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Represents a detected pattern in tender text"""
    pattern_type: str
    pattern_name: str
    confidence: float
    evidence: str
    location: Optional[str] = None


class PatternDetector:
    """
    Detects structural patterns in tender documents to classify them
    as consulting vs goods procurement.
    """
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize pattern definitions"""
        
        # Pattern 1: Evaluation Criteria (Non-Price Heavy)
        self.eval_criteria_patterns = {
            "qcbs_pattern": r"quality\s*(?:and|&)\s*cost\s*based|qcbs",
            "experience_weight": r"experience.*?(\d+)\s*%",
            "technical_weight": r"technical.*?(\d+)\s*%",
            "approach_weight": r"(?:approach|methodology).*?(\d+)\s*%",
            "team_weight": r"(?:team|personnel).*?(\d+)\s*%",
            "price_weight": r"(?:price|cost|financial).*?(\d+)\s*%",
            "evaluation_matrix": r"evaluation\s*(?:criteria|matrix|parameters)",
            "marks_distribution": r"(?:marks|points|score)\s*distribution"
        }
        
        # Pattern 2: Document Requirements (Consulting vs Goods)
        self.doc_patterns = {
            # Consulting indicators
            "capability_statement": r"capability\s*statement",
            "team_cvs": r"(?:cv|resume|bio)\s*(?:of|for)?\s*(?:key|team|consultant)",
            "references": r"(?:client|project)\s*references?",
            "technical_proposal": r"technical\s*proposal",
            "implementation_plan": r"implementation\s*(?:plan|timeline|schedule)",
            "methodology": r"(?:approach|methodology)\s*(?:document|note|proposed)",
            
            # Goods indicators (negative)
            "price_schedule": r"price\s*schedule|rate\s*schedule|bom",
            "delivery_schedule": r"delivery\s*schedule|supply\s*schedule",
            "product_specs": r"product\s*specification|technical\s*specification"
        }
        
        # Pattern 3: SOW Presence and Structure
        self.sow_patterns = {
            "sow_header": r"scope\s*of\s*work|terms\s*of\s*reference|tor\b",
            "phased_approach": r"phase\s*[1-4ivIV]|stage\s*[1-4]",
            "deliverables": r"deliverable[s]?\s*[:\-]|output[s]?\s*[:\-]",
            "milestones": r"milestone[s]?\s*[:\-]|payment\s*milestone",
            "effort_estimation": r"(?:person|man)\s*(?:days?|months?|years?)",
            "consultant_shall": r"(?:consultant|agency|firm)\s*shall",
            "work_packages": r"work\s*package[s]?|wp\s*\d"
        }
        
        # Pattern 4: Duration and Effort
        self.duration_patterns = {
            "months_duration": r"(\d+)\s*months?(?:\s*duration)?",
            "weeks_duration": r"(\d+)\s*weeks?(?:\s*duration)?",
            "person_months": r"(\d+)\s*(?:person|man)\s*months?",
            "person_days": r"(\d+)\s*(?:person|man)\s*days?",
            "fte": r"(\d+\.?\d*)\s*fte|full\s*time\s*equivalent"
        }
        
        # Pattern 5: Contract Type
        self.contract_patterns = {
            # Consulting contract types
            "time_material": r"time\s*(?:and|&)\s*material|t&m|t\+m",
            "fixed_price_deliverables": r"fixed\s*(?:price|fee).*?deliverable",
            "retainer": r"retainer|retained\s*(?:services|consultant)",
            "milestone_based": r"milestone\s*(?:based|payment)",
            "lump_sum": r"lump\s*sum\s*(?:contract|fee|payment)",
            
            # Goods contract types (negative)
            "rate_contract": r"rate\s*contract|rate\s*running\s*contract",
            "supply_order": r"supply\s*order|purchase\s*order",
            "turnkey": r"turnkey\s*(?:contract|project|basis)"
        }
        
        # A&D Specific Patterns
        self.ad_specific_patterns = {
            "defense_acquisition": r"(?:defence|defense)\s*(?:acquisition|procurement)",
            "offset_clause": r"offset\s*(?:clause|policy|requirement)",
            "make_in_india": r"make\s*in\s*india|atmanirbhar|indigenization",
            "dpsu_collaboration": r"dpsu|defence\s*psu|ordnance\s*factory",
            "strategic_partnership": r"strategic\s*partnership|sp\s*model",
            "dpp_compliance": r"dpp|defence\s*procurement\s*procedure",
            "classified_work": r"classified|secret|confidential\s*(?:work|project)"
        }
    
    def detect_all_patterns(self, text: str) -> Dict[str, List[PatternMatch]]:
        """
        Detect all patterns in tender text.
        
        Args:
            text: Full tender text content
            
        Returns:
            Dictionary of pattern categories and their matches
        """
        text_lower = text.lower()
        
        results = {
            "evaluation_criteria": self._detect_evaluation_patterns(text_lower),
            "document_requirements": self._detect_document_patterns(text_lower),
            "sow_structure": self._detect_sow_patterns(text_lower),
            "duration_effort": self._detect_duration_patterns(text_lower),
            "contract_type": self._detect_contract_patterns(text_lower),
            "ad_specific": self._detect_ad_patterns(text_lower)
        }
        
        return results
    
    def _detect_evaluation_patterns(self, text: str) -> List[PatternMatch]:
        """Detect evaluation criteria patterns"""
        matches = []
        
        for pattern_name, pattern in self.eval_criteria_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matches.append(PatternMatch(
                    pattern_type="evaluation_criteria",
                    pattern_name=pattern_name,
                    confidence=0.9 if "weight" in pattern_name else 0.8,
                    evidence=match.group(0)[:100]
                ))
        
        return matches
    
    def _detect_document_patterns(self, text: str) -> List[PatternMatch]:
        """Detect document requirement patterns"""
        matches = []
        
        for pattern_name, pattern in self.doc_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Negative confidence for goods indicators
                is_goods_indicator = pattern_name in ["price_schedule", "delivery_schedule", "product_specs"]
                
                matches.append(PatternMatch(
                    pattern_type="document_requirements",
                    pattern_name=pattern_name,
                    confidence=-0.7 if is_goods_indicator else 0.85,
                    evidence=match.group(0)[:100]
                ))
        
        return matches
    
    def _detect_sow_patterns(self, text: str) -> List[PatternMatch]:
        """Detect SOW structure patterns"""
        matches = []
        
        for pattern_name, pattern in self.sow_patterns.items():
            all_matches = re.findall(pattern, text, re.IGNORECASE)
            if all_matches:
                matches.append(PatternMatch(
                    pattern_type="sow_structure",
                    pattern_name=pattern_name,
                    confidence=0.85,
                    evidence=f"Found {len(all_matches)} occurrences"
                ))
        
        return matches
    
    def _detect_duration_patterns(self, text: str) -> List[PatternMatch]:
        """Detect duration and effort patterns"""
        matches = []
        
        for pattern_name, pattern in self.duration_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                
                # Consulting typically has longer durations
                if pattern_name == "months_duration":
                    months = int(value)
                    confidence = 0.9 if months >= 6 else 0.6 if months >= 3 else 0.3
                elif pattern_name == "person_months":
                    pm = int(value)
                    confidence = 0.95 if pm >= 10 else 0.8 if pm >= 3 else 0.5
                else:
                    confidence = 0.7
                
                matches.append(PatternMatch(
                    pattern_type="duration_effort",
                    pattern_name=pattern_name,
                    confidence=confidence,
                    evidence=match.group(0)[:50]
                ))
        
        return matches
    
    def _detect_contract_patterns(self, text: str) -> List[PatternMatch]:
        """Detect contract type patterns"""
        matches = []
        
        for pattern_name, pattern in self.contract_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Negative confidence for goods contract types
                is_goods_contract = pattern_name in ["rate_contract", "supply_order", "turnkey"]
                
                matches.append(PatternMatch(
                    pattern_type="contract_type",
                    pattern_name=pattern_name,
                    confidence=-0.8 if is_goods_contract else 0.9,
                    evidence=match.group(0)[:50]
                ))
        
        return matches
    
    def _detect_ad_patterns(self, text: str) -> List[PatternMatch]:
        """Detect A&D specific patterns"""
        matches = []
        
        for pattern_name, pattern in self.ad_specific_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matches.append(PatternMatch(
                    pattern_type="ad_specific",
                    pattern_name=pattern_name,
                    confidence=0.95,
                    evidence=match.group(0)[:50]
                ))
        
        return matches
    
    def calculate_consulting_probability(self, patterns: Dict[str, List[PatternMatch]]) -> float:
        """
        Calculate probability that tender is consulting based on patterns.
        
        Returns:
            Probability between 0 and 1
        """
        positive_score = 0
        negative_score = 0
        
        for category, matches in patterns.items():
            for match in matches:
                if match.confidence > 0:
                    positive_score += match.confidence
                else:
                    negative_score += abs(match.confidence)
        
        # Normalize
        total = positive_score + negative_score
        if total == 0:
            return 0.5  # Neutral
        
        probability = positive_score / (positive_score + negative_score)
        return probability
    
    def get_pattern_summary(self, patterns: Dict[str, List[PatternMatch]]) -> List[str]:
        """
        Generate human-readable pattern summary.
        
        Returns:
            List of summary strings
        """
        summary = []
        
        # Count positive and negative patterns
        positive_patterns = []
        negative_patterns = []
        
        for category, matches in patterns.items():
            for match in matches:
                display_name = match.pattern_name.replace("_", " ").title()
                if match.confidence > 0:
                    positive_patterns.append(display_name)
                else:
                    negative_patterns.append(display_name)
        
        if positive_patterns:
            summary.append(f"Consulting indicators: {', '.join(positive_patterns[:5])}")
        
        if negative_patterns:
            summary.append(f"Goods/Supply indicators: {', '.join(negative_patterns[:3])}")
        
        # Special patterns
        ad_patterns = patterns.get("ad_specific", [])
        if ad_patterns:
            ad_names = [p.pattern_name.replace("_", " ").title() for p in ad_patterns]
            summary.append(f"A&D specific: {', '.join(ad_names)}")
        
        return summary


def is_consulting_tender(text: str, threshold: float = 0.65) -> Tuple[bool, float, List[str]]:
    """
    Convenience function to determine if tender is consulting.
    
    Args:
        text: Tender text content
        threshold: Minimum probability to classify as consulting
        
    Returns:
        Tuple of (is_consulting, probability, pattern_summary)
    """
    detector = PatternDetector()
    patterns = detector.detect_all_patterns(text)
    probability = detector.calculate_consulting_probability(patterns)
    summary = detector.get_pattern_summary(patterns)
    
    return probability >= threshold, probability, summary
