"""
A&D Consulting Intelligence - Scoring Configuration
Configuration for A&D relevance scoring algorithm and thresholds

Author: Manoj Gundeti
Last Updated: 2025-12-26
"""

# =============================================================================
# SCORING WEIGHTS
# =============================================================================

SCORING_WEIGHTS = {
    "keyword_match": 0.35,       # 35% - Keyword matching score
    "structural_fit": 0.25,      # 25% - Structural pattern detection
    "budget_alignment": 0.15,    # 15% - Budget range alignment
    "duration_alignment": 0.10,  # 10% - Duration/timeline alignment
    "buyer_alignment": 0.10,     # 10% - Buyer tier alignment
    "capability_gap": 0.05       # 5%  - Capability/expertise fit
}

# =============================================================================
# BUDGET ALIGNMENT CONFIGURATION (in INR)
# =============================================================================

BUDGET_RANGES = {
    "excellent": {
        "min": 50000000,   # ₹5 Crore
        "max": 200000000,  # ₹20 Crore
        "score": 100
    },
    "strong": {
        "min": 10000000,   # ₹1 Crore
        "max": 50000000,   # ₹5 Crore
        "score": 90
    },
    "good": {
        "min": 5000000,    # ₹50 Lakh
        "max": 10000000,   # ₹1 Crore
        "score": 70
    },
    "moderate": {
        "min": 2000000,    # ₹20 Lakh
        "max": 5000000,    # ₹50 Lakh
        "score": 40
    },
    "low": {
        "min": 0,
        "max": 2000000,    # ₹20 Lakh
        "score": 10
    }
}

# =============================================================================
# DURATION ALIGNMENT CONFIGURATION (in months)
# =============================================================================

DURATION_RANGES = {
    "optimal": {
        "min": 12,
        "max": 36,
        "score": 100
    },
    "good": {
        "min": 6,
        "max": 12,
        "score": 80
    },
    "moderate": {
        "min": 3,
        "max": 6,
        "score": 50
    },
    "short": {
        "min": 0,
        "max": 3,
        "score": 20
    }
}

# =============================================================================
# A&D RELEVANCE SCORE INTERPRETATION
# =============================================================================

SCORE_INTERPRETATION = {
    "perfect_fit": {
        "min": 95,
        "max": 100,
        "label": "Perfect Fit",
        "description": "Defense Procurement, Civil Aviation, Modern Strategy",
        "recommendation": "PURSUE"
    },
    "strong_fit": {
        "min": 85,
        "max": 94,
        "label": "Strong Fit",
        "description": "G&PS + A&D alignment",
        "recommendation": "PURSUE"
    },
    "good_fit": {
        "min": 70,
        "max": 84,
        "label": "Good Fit",
        "description": "G&PS + A&D keywords present",
        "recommendation": "PURSUE"
    },
    "moderate_fit": {
        "min": 50,
        "max": 69,
        "label": "Moderate Fit",
        "description": "General G&PS or partial A&D alignment",
        "recommendation": "EVALUATE"
    },
    "weak_fit": {
        "min": 30,
        "max": 49,
        "label": "Weak Fit",
        "description": "G&PS in non-A&D OR A&D in non-consulting",
        "recommendation": "EVALUATE"
    },
    "poor_fit": {
        "min": 0,
        "max": 29,
        "label": "Poor Fit",
        "description": "Likely not A&D consulting",
        "recommendation": "PASS"
    }
}

# =============================================================================
# KEYWORD MATCH SCORING RULES
# =============================================================================

KEYWORD_SCORING = {
    "gps_ad_present": 40,          # Layer 1 + Layer 3 keywords present
    "semantic_consulting": 20,     # Layer 4 synonyms in consulting context
    "ad_modifiers_present": 20,    # A&D modifiers (procurement, strategy, etc.)
    "exclusion_penalty": -20,      # Layer 5 negative keywords detected
    "max_score": 100
}

# =============================================================================
# STRUCTURAL FIT SCORING RULES
# =============================================================================

STRUCTURAL_SCORING = {
    "evaluation_criteria": 30,     # Multi-factor eval (experience, approach, team)
    "detailed_sow": 25,            # SOW with phases and deliverables
    "team_credentials": 25,        # CVs/team qualifications required
    "duration_threshold": 10,      # Duration ≥ 6 months
    "budget_threshold": 10,        # Budget ≥ ₹1 Crore
    "max_score": 100
}

# =============================================================================
# RECOMMENDATION THRESHOLDS
# =============================================================================

RECOMMENDATION_THRESHOLDS = {
    "pursue": {
        "ad_score_min": 75,
        "is_consulting_min": 0.75,
        "budget_min": 10000000,  # ₹1 Crore
        "recommendation": "PURSUE",
        "color": "green"
    },
    "evaluate": {
        "ad_score_min": 50,
        "ad_score_max": 74,
        "is_consulting_min": 0.50,
        "recommendation": "EVALUATE",
        "color": "yellow"
    },
    "pass": {
        "ad_score_max": 49,
        "recommendation": "PASS",
        "color": "red"
    }
}

# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================

CONFIDENCE_THRESHOLDS = {
    "high": {
        "min": 80,
        "action": "auto_process"
    },
    "medium": {
        "min": 50,
        "max": 79,
        "action": "auto_process_with_flag"
    },
    "low": {
        "max": 49,
        "action": "human_review_required"
    }
}

# =============================================================================
# RISK ASSESSMENT CONFIGURATION
# =============================================================================

RISK_LEVELS = ["Low", "Medium", "High"]

RISK_FACTORS = {
    "implementation_risk": {
        "factors": ["complexity", "technology_maturity", "scope_clarity"],
        "weights": [0.4, 0.3, 0.3]
    },
    "scope_creep_risk": {
        "factors": ["sow_clarity", "deliverables_defined", "timeline_buffer"],
        "weights": [0.4, 0.4, 0.2]
    },
    "political_risk": {
        "factors": ["buyer_stability", "funding_source", "election_cycle"],
        "weights": [0.4, 0.4, 0.2]
    },
    "win_probability": {
        "factors": ["capability_match", "relationship", "competition"],
        "weights": [0.4, 0.3, 0.3]
    }
}

# =============================================================================
# CAPABILITY MAPPING
# =============================================================================

FIRM_CAPABILITIES = {
    "strategy": {
        "score": 100,
        "keywords": ["strategy", "advisory", "planning", "roadmap"]
    },
    "digital_transformation": {
        "score": 95,
        "keywords": ["digital", "transformation", "modernization", "automation"]
    },
    "defense_consulting": {
        "score": 90,
        "keywords": ["defense", "procurement", "acquisition", "modernization"]
    },
    "aerospace": {
        "score": 85,
        "keywords": ["aviation", "aerospace", "airport", "airline"]
    },
    "cybersecurity": {
        "score": 80,
        "keywords": ["cyber", "security", "c4isr", "information security"]
    },
    "process_optimization": {
        "score": 90,
        "keywords": ["process", "optimization", "lean", "efficiency"]
    },
    "pmu": {
        "score": 95,
        "keywords": ["pmu", "project management", "implementation", "monitoring"]
    },
    "training": {
        "score": 85,
        "keywords": ["training", "capacity building", "skill development"]
    }
}


def get_budget_score(budget_inr: float) -> int:
    """Calculate budget alignment score"""
    for range_name, config in BUDGET_RANGES.items():
        if config["min"] <= budget_inr <= config["max"]:
            return config["score"]
        elif budget_inr > config["max"] and range_name == "excellent":
            return 100  # Above excellent range is still excellent
    return 10  # Default low score


def get_duration_score(duration_months: int) -> int:
    """Calculate duration alignment score"""
    for range_name, config in DURATION_RANGES.items():
        if config["min"] <= duration_months <= config["max"]:
            return config["score"]
        elif duration_months > config["max"] and range_name == "optimal":
            return 100  # Longer than optimal is still good
    return 20  # Default short score


def get_recommendation(ad_score: float, is_consulting: float, budget: float) -> str:
    """Determine recommendation based on thresholds"""
    if (ad_score >= RECOMMENDATION_THRESHOLDS["pursue"]["ad_score_min"] and
        is_consulting >= RECOMMENDATION_THRESHOLDS["pursue"]["is_consulting_min"] and
        budget >= RECOMMENDATION_THRESHOLDS["pursue"]["budget_min"]):
        return "PURSUE"
    elif (ad_score >= RECOMMENDATION_THRESHOLDS["evaluate"]["ad_score_min"] and
          is_consulting >= RECOMMENDATION_THRESHOLDS["evaluate"]["is_consulting_min"]):
        return "EVALUATE"
    else:
        return "PASS"


def get_score_interpretation(score: float) -> dict:
    """Get interpretation for a given A&D relevance score"""
    for level_name, config in SCORE_INTERPRETATION.items():
        if config["min"] <= score <= config["max"]:
            return {
                "level": level_name,
                "label": config["label"],
                "description": config["description"],
                "recommendation": config["recommendation"]
            }
    return {
        "level": "poor_fit",
        "label": "Poor Fit",
        "description": "Unknown classification",
        "recommendation": "PASS"
    }


def get_capability_score(text: str) -> int:
    """Calculate capability/expertise alignment score"""
    text_lower = text.lower()
    best_score = 40  # Default: requires building new capability
    
    for capability, config in FIRM_CAPABILITIES.items():
        for keyword in config["keywords"]:
            if keyword.lower() in text_lower:
                if config["score"] > best_score:
                    best_score = config["score"]
                break
    
    return best_score
