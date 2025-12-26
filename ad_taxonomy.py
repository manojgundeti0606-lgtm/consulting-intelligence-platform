"""
A&D Consulting Intelligence - 5-Layer Keyword Taxonomy
Comprehensive keyword sets for G&PS and A&D tender classification

Author: Manoj Gundeti
Last Updated: 2025-12-26
"""

# =============================================================================
# LAYER 1: GOVERNMENT & PUBLIC SECTOR IDENTIFIERS
# =============================================================================

GPS_IDENTIFIERS = {
    "strong": {  # Confidence 95%+
        "keywords": [
            "government", "ministry", "department", "state government",
            "central government", "psu", "public sector", "government of india",
            "government agency", "government ministry", "government organization",
            "government undertaking", "govt", "govt.", "sarkari"
        ],
        "confidence": 0.95
    },
    "medium": {  # Confidence 80%
        "keywords": [
            "apex body", "statutory authority", "regulatory body", 
            "autonomous body", "government corporation", "national institute",
            "government scheme", "public undertaking", "central public sector",
            "state public sector", "cpse", "spse"
        ],
        "confidence": 0.80
    }
}

# =============================================================================
# LAYER 2: CONSULTING SERVICES IDENTIFIERS
# =============================================================================

CONSULTING_KEYWORDS = {
    "consulting_terms": [
        "consulting", "consultancy", "management consulting", "consulting services",
        "professional services", "advisory services", "strategic advisory",
        "expert services", "technical assistance", "ta", "advisory"
    ],
    
    "study_assessment": [
        "feasibility study", "detailed project report", "dpr", "assessment",
        "appraisal", "evaluation", "study", "research", "analysis", "diagnostic",
        "gap analysis", "benchmarking", "survey", "review", "audit"
    ],
    
    "strategy_planning": [
        "strategic planning", "strategy development", "roadmap", "technology roadmap",
        "master plan", "policy formulation", "vision document", "policy development",
        "strategic framework", "blueprint", "future state", "transformation agenda",
        "strategic direction", "action plan"
    ],
    
    "implementation_support": [
        "implementation support", "implementation assistance", "project management unit",
        "pmu", "implementation monitoring", "change management", "transition support",
        "program management", "project management", "pmo"
    ],
    
    "capacity_building": [
        "training", "capacity building", "skill development", "training program",
        "capability development", "competency development", "knowledge transfer",
        "workshop", "handholding", "mentoring"
    ],
    
    "specialized": [
        "organizational restructuring", "organizational design", "process optimization",
        "process improvement", "due diligence", "financial advisory", "audit",
        "compliance advisory", "restructuring", "reengineering", "transformation"
    ]
}

# =============================================================================
# LAYER 3: AEROSPACE & DEFENSE KEYWORDS
# =============================================================================

AD_KEYWORDS = {
    "defense": [
        "defence", "defense", "military", "armed forces", "mod",
        "ministry of defence", "department of defence", "drdo",
        "defence research", "ordnance factory", "naval", "navy", "army",
        "iaf", "indian air force", "coast guard", "national security",
        "defense strategy", "acquisition", "weapons system", "combat",
        "tactical", "operational capability", "atmanirbhar bharat",
        "make in india", "indigenization", "pqis", "defense manufacturing",
        "defense contractor", "military modernization", "armed services"
    ],
    
    "aerospace": [
        "aerospace", "aviation", "aircraft", "civil aviation",
        "ministry of civil aviation", "mca", "aai", "airports authority",
        "hal", "hindustan aeronautics", "airline", "airport", "air navigation",
        "aircraft maintenance", "mro", "maintenance repair overhaul",
        "aviation safety", "dgca", "airport infrastructure", "airfield",
        "air cargo", "flight operations", "pilot training", "atc",
        "air traffic control"
    ],
    
    "ad_infrastructure": [
        "ordnance factory", "ammunition", "naval shipbuilding", "naval dockyard",
        "ship", "vessel", "launch vehicle", "space", "isro", "missile",
        "ballistic", "air defense", "radar", "electronic warfare",
        "communication system", "command control", "c4isr", "satellite"
    ],
    
    "ad_process_capability": [
        "acquisition", "procurement strategy", "vendor evaluation",
        "supply chain", "logistics", "defense manufacturing", "production",
        "quality assurance", "arai", "arai certification", "bis", "nadcap",
        "as9100", "defense standards", "military standards", "cost control",
        "project management", "risk management", "defense compliance",
        "defense financial management", "defense audit"
    ],
    
    "ad_buyers": [
        "ministry of defence", "department of aerospace",
        "department of defence production", "drdo", "ordnance factory board",
        "hal", "bel", "hindustan shipyard", "mazagon dock", "cochin shipyard",
        "garden reach shipbuilders", "midhani", "army headquarters",
        "naval headquarters", "air force headquarters", "coast guard headquarters",
        "isro", "ministry of civil aviation", "airports authority", "dgca",
        "air navigation services", "director general of shipping", "beml",
        "bharat dynamics", "gsl", "grse"
    ]
}

# Buyer Tier Classification
AD_BUYER_TIERS = {
    "tier_1": {  # Score: 100
        "buyers": [
            "ministry of defence", "mod", "drdo", "hal", "bel",
            "army headquarters", "naval headquarters", "air force headquarters",
            "indian army", "indian navy", "indian air force"
        ],
        "score": 100
    },
    "tier_2": {  # Score: 90
        "buyers": [
            "ordnance factory", "hindustan shipyard", "mazagon dock",
            "cochin shipyard", "garden reach", "midhani", "bharat dynamics",
            "department of defence production", "beml", "gsl", "grse"
        ],
        "score": 90
    },
    "tier_3": {  # Score: 80
        "buyers": [
            "ministry of civil aviation", "aai", "airports authority",
            "dgca", "isro", "air navigation services", "antrix"
        ],
        "score": 80
    },
    "tier_4": {  # Score: 60
        "buyers": [
            "state government", "autonomous body", "defence psu",
            "aerospace company", "defense institute"
        ],
        "score": 60
    },
    "tier_5": {  # Score: 40
        "buyers": [
            "government", "ministry", "department", "psu", "cpse"
        ],
        "score": 40
    }
}

# =============================================================================
# LAYER 4: SEMANTIC EXPANSION
# =============================================================================

SEMANTIC_EXPANSION = {
    "erp_enterprise": [
        "erp", "enterprise resource planning", "sap", "oracle", "baan", "ifs",
        "infor", "business system", "accounting system", "finance system",
        "supply chain system", "integrated system", "aerospace erp",
        "manufacturing system", "mrp"
    ],
    
    "cloud_infrastructure": [
        "cloud", "cloud migration", "cloud adoption", "aws", "azure", "gcp",
        "public cloud", "private cloud", "hybrid cloud", "on-premise",
        "infrastructure", "virtual infrastructure", "secure cloud",
        "classified cloud", "defense cloud", "restricted cloud", "data center"
    ],
    
    "digital_transformation": [
        "digital", "digitization", "digital transformation", "paperless",
        "modernization", "automation", "process automation", "workflow",
        "e-process", "e-governance", "smart system", "defense digitalization",
        "cyber-enabled", "industry 4.0", "iot", "ai", "machine learning"
    ],
    
    "cybersecurity": [
        "cybersecurity", "cyber", "security", "information security", "it security",
        "ciso", "c4isr", "cyber defense", "cyber resilience", "cyber strategy",
        "threat intelligence", "penetration testing", "security audit",
        "operational security", "tempest", "secured networks", "soc", "siem"
    ],
    
    "business_intelligence": [
        "analytics", "business intelligence", "bi", "data analytics", "reporting",
        "dashboard", "kpi", "metrics", "visualization", "data warehouse",
        "operational intelligence", "predictive analytics", "big data"
    ],
    
    "process_optimization": [
        "optimization", "efficiency", "improvement", "streamlining", "lean",
        "six sigma", "bpm", "process reengineering", "best practice",
        "enhancement", "acceleration", "tqm", "kaizen"
    ],
    
    "strategic_planning": [
        "strategy", "strategic plan", "planning", "vision", "direction",
        "blueprint", "framework", "charter", "strategic direction",
        "future state", "transformation agenda", "roadmap"
    ]
}

# =============================================================================
# LAYER 5: NEGATIVE KEYWORDS (EXCLUSIONS)
# =============================================================================

NEGATIVE_KEYWORDS = {
    "hard_exclusions": [  # Definitely NOT consulting - reject
        "supply of", "procurement of", "purchase of", "hardware",
        "equipment", "machinery", "tools", "components", "spare parts",
        "software license", "software subscription", "amc",
        "annual maintenance contract", "rent", "lease", "rental",
        "manufacturing", "production", "fabrication", "construction",
        "civil works", "building", "installation", "commissioning",
        "repair", "maintenance", "servicing", "courier", "transportation",
        "housekeeping", "janitorial", "facilities management",
        "vendor registration", "vendor approval", "data entry",
        "data processing", "temporary staff", "manpower supply",
        "staffing", "labour supply", "catering", "canteen", "security guard"
    ],
    
    "soft_exclusions": [  # Context-dependent - check further
        "it services",  # Check if advisory or staff augmentation
        "software development",  # Check if custom dev or advisory
        "implementation",  # Check if advisory or pure execution
        "system integration",  # Check if strategic or purely technical
        "outsourcing",  # Check if advisory on outsourcing or service delivery
        "bpo", "kpo", "resource augmentation"
    ]
}

# =============================================================================
# A&D SUB-CATEGORY DEFINITIONS
# =============================================================================

AD_SUBCATEGORIES = {
    "defense_procurement_strategy": {
        "name": "Defense Procurement & Strategy",
        "keywords": [
            "acquisition", "procurement strategy", "vendor evaluation",
            "defense strategy", "supply chain", "weapons", "procurement process",
            "contract management", "offset", "indigenous"
        ],
        "typical_buyers": ["mod", "department of defence production"],
        "budget_range": (50000000, 500000000),  # ₹5Cr-₹50Cr
        "signals": ["vendor management", "procurement optimization", "risk management"]
    },
    
    "military_modernization": {
        "name": "Military Modernization",
        "keywords": [
            "modernization", "capability", "strategy", "technology roadmap",
            "defense modernization", "operational effectiveness", "force development",
            "capability development"
        ],
        "typical_buyers": ["armed services", "drdo", "mod"],
        "budget_range": (50000000, 200000000),  # ₹5Cr-₹20Cr
        "signals": ["technology assessment", "capability planning", "modernization roadmap"]
    },
    
    "civil_aviation": {
        "name": "Civil Aviation",
        "keywords": [
            "civil aviation", "airline", "airport", "dgca", "aviation sector",
            "air navigation", "airport infrastructure", "atc", "mro"
        ],
        "typical_buyers": ["ministry of civil aviation", "aai", "dgca"],
        "budget_range": (20000000, 100000000),  # ₹2Cr-₹10Cr
        "signals": ["airport planning", "aviation strategy", "regulatory compliance"]
    },
    
    "defense_manufacturing": {
        "name": "Defense Manufacturing & Production",
        "keywords": [
            "manufacturing", "production", "supply chain", "lean", "quality assurance",
            "arai", "defense manufacturing", "ordnance", "indigenous production"
        ],
        "typical_buyers": ["ordnance factory", "defense psu", "hal", "bel"],
        "budget_range": (10000000, 50000000),  # ₹1Cr-₹5Cr
        "signals": ["process improvement", "manufacturing optimization", "quality systems"]
    },
    
    "cybersecurity_c4isr": {
        "name": "Cybersecurity & C4ISR",
        "keywords": [
            "cybersecurity", "cyber", "c4isr", "command control",
            "information security", "defense it", "secure communications"
        ],
        "typical_buyers": ["mod", "armed services", "drdo", "defense psu"],
        "budget_range": (5000000, 30000000),  # ₹50L-₹3Cr
        "signals": ["security assessment", "strategy", "implementation support"]
    },
    
    "regulatory_compliance": {
        "name": "Regulatory & Compliance",
        "keywords": [
            "certification", "arai", "bis", "nadcap", "as9100",
            "standards", "compliance", "audit", "regulatory"
        ],
        "typical_buyers": ["defense psu", "manufacturing entities", "hal"],
        "budget_range": (2000000, 10000000),  # ₹20L-₹1Cr
        "signals": ["certification support", "standards implementation", "audit"]
    }
}

# =============================================================================
# CONSULTING CATEGORY DEFINITIONS
# =============================================================================

CONSULTING_CATEGORIES = {
    "strategy": {
        "name": "Strategy",
        "keywords": ["strategy", "strategic", "vision", "roadmap", "planning", "advisory"]
    },
    "digital": {
        "name": "Digital",
        "keywords": ["digital", "technology", "it", "automation", "cloud", "analytics"]
    },
    "pmu": {
        "name": "PMU",
        "keywords": ["pmu", "project management", "implementation", "monitoring", "program"]
    },
    "audit": {
        "name": "Audit",
        "keywords": ["audit", "compliance", "review", "assessment", "evaluation"]
    },
    "training": {
        "name": "Training",
        "keywords": ["training", "capacity building", "skill", "workshop", "knowledge transfer"]
    }
}


def get_all_consulting_keywords() -> set:
    """Get flattened set of all consulting keywords"""
    keywords = set()
    for category in CONSULTING_KEYWORDS.values():
        keywords.update([k.lower() for k in category])
    return keywords


def get_all_ad_keywords() -> set:
    """Get flattened set of all A&D keywords"""
    keywords = set()
    for category in AD_KEYWORDS.values():
        keywords.update([k.lower() for k in category])
    return keywords


def get_all_negative_keywords() -> set:
    """Get flattened set of all negative keywords (hard + soft)"""
    keywords = set()
    keywords.update([k.lower() for k in NEGATIVE_KEYWORDS["hard_exclusions"]])
    keywords.update([k.lower() for k in NEGATIVE_KEYWORDS["soft_exclusions"]])
    return keywords


def get_buyer_tier(buyer_name: str) -> tuple:
    """Get buyer tier and score based on buyer name"""
    buyer_lower = buyer_name.lower()
    
    for tier_name, tier_data in AD_BUYER_TIERS.items():
        for buyer_keyword in tier_data["buyers"]:
            if buyer_keyword.lower() in buyer_lower:
                return tier_name, tier_data["score"]
    
    return "tier_5", 40  # Default to general government


def classify_ad_subcategory(text: str, keywords_matched: list) -> tuple:
    """Classify tender into A&D sub-category"""
    text_lower = text.lower()
    best_match = None
    best_score = 0
    
    for subcat_id, subcat_data in AD_SUBCATEGORIES.items():
        score = 0
        for keyword in subcat_data["keywords"]:
            if keyword.lower() in text_lower:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = subcat_id
    
    if best_match:
        return best_match, AD_SUBCATEGORIES[best_match]["name"]
    
    return "defense_procurement_strategy", "Defense Procurement & Strategy"


def classify_consulting_category(text: str) -> str:
    """Classify into consulting category"""
    text_lower = text.lower()
    best_category = "strategy"
    best_score = 0
    
    for cat_id, cat_data in CONSULTING_CATEGORIES.items():
        score = sum(1 for kw in cat_data["keywords"] if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best_category = cat_id
    
    return CONSULTING_CATEGORIES[best_category]["name"]
