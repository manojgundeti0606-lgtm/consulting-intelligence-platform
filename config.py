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
    "enable_slack": False,
    "team_emails": [
        "atul.shukla1@in.ey.com",
        "vinayak.mishra1@in.ey.com",
        "arjun.anand@in.ey.com"
    ]
}

import os
from dotenv import load_dotenv

# Load local .env if it exists
load_dotenv()

# Database Configuration
DATABASE_CONFIG = {
    "db_type": os.getenv("DATABASE_TYPE", "sqlite"), # 'sqlite' or 'postgres'
    "db_path": os.getenv("DB_PATH", "cip_data.db"),
    "backup_enabled": True,
    "backup_interval_days": 7,
    
    # PostgreSQL / Cloud SQL Settings
    "postgres": {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "cip_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "use_cloud_sql_proxy": os.getenv("USE_CLOUD_SQL_PROXY", "False").lower() == "true",
        "instance_connection_name": os.getenv("DB_INSTANCE_CONNECTION_NAME", "")
    }
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

# Ministry of Defence (MoD) Organizations - For targeted Defence tender scraping
MOD_ORGANIZATIONS = [
    # Armed Forces & Academies (1-10)
    "Indian Air Force",
    "Airforce Academy",
    "Armed Forces Films and Photo Division",
    "Armed Forces Headquarters Civil Services",
    "Armed Forces Medical College (India), Pune",
    "Armed Forces Medical Services",
    "Armed Forces Tribunal",
    "Indian army",
    "Army Purchase Organisation",
    "Border Roads Engineering Service",
    
    # Border & Cantonment (11-26)
    "Border Roads Organisation",
    "Canteen Stores Department (CSD)",
    "Cantonment Board, Aurangabad, Maharashtra",
    "Cantonment Board, Delhi",
    "Cantonment Board, Deolali, Maharashtra",
    "Cantonment Board, Faizabad, Uttar Pradesh",
    "Cantonment Board, Fatehgarh, Uttar Pradesh",
    "Cantonment Board, Jabalpur, Madhya Pradesh",
    "Cantonment Board, Jalandhar, Punjab",
    "Cantonment Board, Kamptee, Maharashtra",
    "Cantonment Board, Kanpur, Uttar Pradesh",
    "Cantonment Board, Lansdowne, Uttarakhand",
    "Cantonment Board, Lucknow, Uttar Pradesh",
    "Cantonment Board, Pachmarhi, Madhya Pradesh",
    "Cantonment Board, Shillong, Meghalaya",
    "College of Defence Management, Secunderabad",
    
    # Defence Departments & Agencies (27-45)
    "Defence Accounts Department",
    "Defence Aeronautical Quality Assurance Service",
    "Defence Cyber Agency",
    "Defence Institute of Advanced Technology",
    "Defence Institute of Psychological Research",
    "Defence Quality Assurance Service",
    "Defence Research and Development Service",
    "Defence Services Staff College, Wellington Cantonment, The Nilgiris",
    "Defence Space Research Agency (DSRA)",
    "Department of Defence (DOD)",
    "Department of Defence Production (DDP)",
    "Defence Research and Development Organisation (DRDO)",
    "Department of Ex-Servicemen Welfare",
    "Department of Military Affairs (DMA)",
    "Directorate General of Defence Estates, New Delhi",
    "Directorate General Quality Assurance",
    "Directorate General Resettlement, New Delhi",
    "History Division, MoD",
    "Indian Coast Guard",
    
    # Indian Defence Services (46-56)
    "Indian Defence Accounts Service",
    "Indian Defence Contract Management Service",
    "Indian Defence Estates Service",
    "Indian Defence Service of Engineers",
    "Indian Military Academy, Dehradun",
    "Indian Naval Academy",
    "Indian Naval Armament Service",
    "Indian Ordnance Factories Health Service",
    "Indian Ordnance Factories Service",
    "Institute for Defence Studies and Analyses",
    "Military Engineer Services",
    
    # Training & Educational Institutions (57-67)
    "Military Institute of Technology (MILIT), Pune",
    "Ministry of Defence Library",
    "National Cadet Corps",
    "National Defence Academy, Pune",
    "National Defence College, New Delhi",
    "National Defence University",
    "Indian Navy",
    "Officers Training Academy, Chennai & Gaya",
    "Rashtriyaa Indian Military College R.I.M.C",
    "Rashtriya Military Schools",
    "Recruitment and Assessment Centre (RAC), Defence Research and Development Organisation DRDO",
    
    # Special Divisions & Commands (68-76)
    "Services Sports Control Board",
    "St.Thomas Mount cum Pallavaram Cantonment Board, Tamil nadu",
    "Strategic Information Services",
    "Tactical Intelligence Division",
    "Sainik Schools",
    "Defence Image Processing and Analysis Centre DIPAC",
    "HQ Integrated Defence Staff",
    "Strategic Forces Command",
    
    # Army Commands (77-83)
    "Central Command- Indian Army",
    "Eastern Command- Indian Army",
    "Northern Command- Indian Army",
    "Southern Command- Indian Army",
    "South Western Command- Indian Army",
    "Western Command- Indian Army",
    "Army Training Command- Indian Army",
    
    # Naval Commands (84-86)
    "Western Naval Command- Indian Navy",
    "Eastern Naval Command- Indian Navy",
    "Southern Naval Command- Indian Navy",
    
    # Air Force Commands (87-93)
    "Western Air Command- Indian Air Force",
    "Central Air Command- Indian Air Force",
    "South Western Air Command- Indian Air Force",
    "Eastern Air Command- Indian Air Force",
    "Southern Air Command- Indian Air Force",
    "Training Command- Indian Air Force",
    "Maintenance Command- Indian Air Force",
    
    # Joint Commands & Welfare Associations (94-96)
    "Andaman Nicobar Command",
    "Army Wives Welfare Association",
    "Navy Wives Welfare Association",
    "Air Force Wives Welfare Association",
]

# Defence Public Sector Undertakings (DPSUs) and their units
DEFENCE_PSUS = [
    # Existing DPSUs
    "Bharat Earth Movers Limited BEML",
    "Bharat Electronics Limited BEL",
    "Garden Reach Shipbuilders and Engineers Limited GRSE",
    "Goa Shipyard Limited",
    "Hindustan Aeronautics Limited HAL",
    "Hindustan Shipyard Limited HSL",
    "Mazagon Dock Shipbuilders Limited",
    "Bharat Dynamics Ltd",
    "Mishra Dhatu Nigam Ltd MIDHANI",
    
    # ===== 7 New DPSUs (from OFB) =====
    
    # 1. Munitions India Limited (MIL)
    "Munitions India Limited", "MIL",
    "Munitions India Limited Headquarters Pune", "MILHQ",
    "Ammunition Factory Khadki", "AFK",
    "Cordite Factory Aruvankadu", "CFA",
    "High Energy Projectile Factory Tiruchirapalli", "HEPF",
    "High Explosive Factory Khadki", "HEF",
    "Ordnance Factory Bhandara", "OFBA",
    "Ordnance Factory Badmal", "OFBOL",
    "Ordnance Factory Chanda", "OFCH",
    "Ordnance Factory Dehu Road", "OFDR",
    "Ordnance Factory Itarsi", "OFI",
    "Ordnance Factory Khamaria", "OFK",
    "Ordnance Factory Nalanda", "OFN",
    "Ordnance Factory Varangaon", "OFV",
    "Munitions India Limited Controllerate of Safety", "MILCOS",
    "National Academy of Defence Production", "NADP",
    "Ordnance Factory Institute of Learning Khamaria", "OFILKH",
    
    # 2. Armoured Vehicles Nigam Limited (AVNL)
    "Armoured Vehicles Nigam Limited", "AVNL",
    "Armoured Vehicles Nigam Limited Headquarters Avadi", "AVNLHQ",
    "Engine Factory Avadi", "EFA",
    "Heavy Vehicle Factory Avadi", "HVF",
    "Machine Tool Prototype Factory Ambarnath", "MPF",
    "Ordnance Factory Medak", "OFMK",
    "Vehicle Factory Jabalpur", "VFJ",
    "AVNL Institute of Learning Ambarnath", "AVNLIOLAM",
    "AVNL Institute of Learning Avadi", "AVNLIOLAV",
    "AVNL Institute of Learning Medak", "AVNLIOLMK",
    
    # 3. Advanced Weapons and Equipment India Limited (AWEIL)
    "Advanced Weapons and Equipment India Limited", "AWEIL",
    "Advanced Weapons and Equipment India Limited Headquarters", "AWEILHQ",
    "Field Gun Factory Kanpur", "FGK",
    "Gun Carriage Factory Jabalpur", "GCF",
    "Gun Shell Factory Cossipore", "GSF",
    "Ordnance Factory Kanpur", "OFC",
    "Ordnance Factory Project Korwa", "OFPKR",
    "Ordnance Factory Tiruchirapalli", "OFT",
    "Rifle Factory Ishapore", "RFI",
    "Small Arms Factory Kanpur", "SAF",
    "Academy of Weapons Technology and Management Ichapore", "AWTM",
    
    # 4. Troop Comforts Limited (TCL)
    "Troop Comforts Limited", "TCL",
    "Troop Comforts Limited Headquarters Kanpur", "TCLHQ",
    "Ordnance Clothing Factory Avadi", "OCFAV",
    "Ordnance Clothing Factory Shahjahanpur", "OCFS",
    "Ordnance Equipment Factory Kanpur", "OEFC",
    "Ordnance Equipment Factory Hazratpur", "OEFHZ",
    "Troop Comforts Limited Training Academy Kanpur", "TCLTA",
    
    # 5. Yantra India Limited (YIL)
    "Yantra India Limited", "YIL",
    "Yantra India Limited Headquarters Ambajhari", "YILHQ",
    "Metal Steel Factory", "MSF",
    "Ordnance Factory Ambarnath", "OFA",
    "Ordnance Factory Ambajhari", "OFAJ",
    "Ordnance Factory Bhusawal", "OFBH",
    "Ordnance Factory Dum Dum", "OFDC",
    "Ordnance Factory Jabalpur", "OFJ",
    "Ordnance Factory Katni", "OFKAT",
    "Ordnance Factory Muradnagar", "OFM",
    "Yantra Institute of Technology and Management Ambajhari", "YITM",
    "Yantra Business Development Centre New Delhi", "YBDC",
    "Yantra India Limited Kolkata Office Ishapore", "YILKO",
    
    # 6. India Optel Limited (IOL)
    "India Optel Limited", "IOL",
    "India Optel Limited Headquarters Dehradun", "IOLHQ",
    "Ordnance Factory Chandigarh", "OFCD",
    "Ordnance Factory Dehradun", "OFDUN",
    "Opto Electronic Factory Dehradun", "OLF",
    "Ordnance Factory Institute of Learning Dehradun", "OFIOLDD",
    
    # 7. Gliders India Limited (GIL)
    "Gliders India Limited", "GIL",
    "Gliders India Limited Headquarters Kanpur", "GILHQ",
    "Ordnance Parachute Factory Kanpur", "OPF",
]

# Combined list for searching
ALL_DEFENCE_ORGANIZATIONS = MOD_ORGANIZATIONS + DEFENCE_PSUS

# Short keywords for efficient matching (extracted from organization names)
DEFENCE_ORG_KEYWORDS = [
    # General Defence terms
    "defence", "defense", "military", "armed forces", "MoD",
    
    # Service branches
    "indian army", "indian navy", "indian air force", "coast guard",
    "army", "navy", "air force", "IAF", "NCC",
    
    # Key organizations
    "DRDO", "BEL", "HAL", "BEML", "ordnance", "cantonment",
    "border roads", "BRO", "MES", "military engineer",
    
    # Commands
    "command", "naval command", "air command",
    
    # Institutes & Academies
    "defence academy", "NDA", "IMA", "sainik", "military academy",
    
    # DPSUs
    "GRSE", "Goa Shipyard", "Mazagon Dock", "HSL", "Bharat Dynamics",
    "MIDHANI", "Munition India", "AVNL", "AWEIL",
]
