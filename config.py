"""
Configuration module for Consulting Intelligence Platform
Contains consulting taxonomy, firm profile, and system settings
"""

# Consulting Taxonomy - Category Definitions
CONSULTING_TAXONOMY = {
    "Strategy & Policy": {
        "primary_keywords": [
            "consultancy", "advisory", "feasibility study", "dpr", "detailed project report",
            "vision document", "roadmap", "policy formulation", "strategic planning",
            "business plan", "master plan", "framework development"
        ],
        "secondary_context": ["report", "strategy", "plan", "framework", "study"],
        "exclude_keywords": ["supply", "procurement of goods", "equipment", "hardware"]
    },
    "Tech & Digital": {
        "primary_keywords": [
            "system integrator", "si", "managed services", "cloud migration",
            "cybersecurity audit", "erp", "enterprise resource planning",
            "dashboard development", "web portal", "mobile app", "software development",
            "digital transformation", "e-governance", "it modernization", "automation",
            "artificial intelligence", "machine learning", "data analytics"
        ],
        "secondary_context": ["implementation", "services", "solution", "platform", "system"],
        "exclude_keywords": ["hardware supply", "equipment procurement", "computer supply"]
    },
    "PMU / PMC": {
        "primary_keywords": [
            "project management unit", "pmu", "pmc", "project management consultant",
            "support agency", "manpower support", "outsourcing", "resource deployment",
            "project monitoring", "implementation support"
        ],
        "secondary_context": ["resource deployment", "sla", "manpower", "support"],
        "exclude_keywords": []
    },
    "Audit & Finance": {
        "primary_keywords": [
            "statutory audit", "transaction advisory", "financial modeling",
            "due diligence", "tax consultant", "chartered accountant", "ca firm",
            "financial audit", "internal audit", "compliance audit", "financial advisor"
        ],
        "secondary_context": ["audit", "financial", "advisory", "compliance"],
        "exclude_keywords": []
    },
    "HR & Capacity": {
        "primary_keywords": [
            "capacity building", "training", "hr audit", "change management",
            "recruitment agency", "talent management", "organizational development",
            "skill development", "workshop", "learning development"
        ],
        "secondary_context": ["training", "capacity", "development", "skills", "transformation"],
        "exclude_keywords": []
    }
}

# EY Consulting Firm Profile
FIRM_PROFILE = {
    "name": "EY Consulting",
    "expertise_areas": [
        "Business Consulting",
        "Technology Consulting",
        "Digital Transformation",
        "Strategy & Transactions",
        "People Advisory Services",
        "M&A Advisory",
        "Cloud Migration",
        "Cybersecurity",
        "AI & Advanced Analytics",
        "ERP Implementation",
        "Supply Chain Optimization",
        "Organization Transformation",
        "Public Sector Consulting",
        "IT Modernization",
        "E-Governance"
    ],
    "industries": [
        "Financial Services",
        "Public Sector",
        "Healthcare",
        "Energy & Resources",
        "Technology & Media",
        "Consumer & Retail",
        "Manufacturing",
        "Telecommunications"
    ],
    "technology_stack": [
        "Cloud Platforms (AWS, Azure, GCP)",
        "ERP Systems (SAP, Oracle)",
        "AI/ML Technologies",
        "Data Analytics Platforms",
        "Cybersecurity Solutions",
        "Automation Tools",
        "DevOps & Agile",
        "Business Intelligence"
    ],
    "turnover_threshold": 0,  # Minimum bid value in INR (0 = no limit)
    "preferred_categories": [
        "Strategy & Policy",
        "Tech & Digital",
        "PMU / PMC"
    ]
}

# Scraping Configuration
SCRAPING_CONFIG = {
    "max_pages": 0, # 0 = Unlimited pages
    "rate_limit_min": 2,  # seconds
    "rate_limit_max": 5,  # seconds
    "retry_attempts": 3,
    "retry_backoff": 2,  # exponential backoff multiplier
    "consulting_only": True
}

# AI Analysis Configuration
AI_CONFIG = {
    "model": "models/gemini-3-flash-preview",  # Gemini 3.0 Flash Preview
    "fast_model": "models/gemini-2.0-flash",            # Fast scanning
    "temperature": 0.3,
    "max_tokens": 8192,               # Increased for larger summaries
    "timeout": 60,
    "retry_attempts": 5
}

# Scheduler Configuration
SCHEDULER_CONFIG = {
    "daily_run_time": "08:00",  # HH:MM format
    "watchlist_interval_hours": 6,
    "timezone": "Asia/Kolkata"
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    "digest_format": "json",  # json or markdown
    "digest_path": "digests",
    "min_cfs_score": 50,  # Only include bids with CFS >= 50 in digest
    "enable_email": True,  # Send email digest after daily scrape
    "enable_slack": False
}

# Database Configuration
DATABASE_CONFIG = {
    "db_path": "cip_data.db",
    "backup_enabled": True,
    "backup_interval_days": 7
}

# Keyword Expansion Mappings
KEYWORD_EXPANSIONS = {
    "digital transformation": ["e-governance", "it modernization", "digitalization", "digital india"],
    "erp": ["enterprise resource planning", "sap", "oracle", "erp implementation"],
    "cloud": ["cloud migration", "cloud computing", "aws", "azure", "gcp"],
    "ai": ["artificial intelligence", "machine learning", "ai/ml", "data analytics"],
    "cyber": ["cybersecurity", "information security", "cyber security", "it security"],
    "pmu": ["project management unit", "pmc", "project management consultant"],
    "consultancy": ["advisory", "consulting services", "consultant"],
    "smart city": ["smart cities", "smart city mission", "urban development"],
    "e-governance": ["digital governance", "e-gov", "government digitalization"]
}
