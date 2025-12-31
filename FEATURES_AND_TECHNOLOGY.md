# Consulting Intelligence Platform (CIP)

## Features & Technology Stack Documentation

---

## 🏗️ Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Streamlit** | ≥1.28.0 | Python-based web UI framework |
| **HTML/CSS** | Custom | Professional EY-themed styling with glassmorphism effects |
| **Google Fonts** | Inter | Modern typography |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.7+ | Core programming language |
| **SQLite** | Built-in | Local database for bids, analysis, and watchlist |
| **APScheduler** | ≥3.10.0 | Background job scheduling for automated scraping |

### AI & ML

| Technology | Version | Purpose |
|------------|---------|---------|
| **Google Gemini** | 2.5 Flash | AI-powered bid analysis, scoring, and summarization |
| **google-generativeai** | ≥0.3.0 | Python SDK for Gemini API |

### Data Processing

| Technology | Version | Purpose |
|------------|---------|---------|
| **Pandas** | ≥2.0.0 | Data manipulation and CSV export |
| **pdfplumber** | ≥0.10.0 | PDF text extraction for SOW analysis |
| **BeautifulSoup4** | ≥4.12.0 | HTML parsing for web scraping |

### Web Scraping

| Technology | Version | Purpose |
|------------|---------|---------|
| **Requests** | ≥2.31.0 | HTTP requests to GeM and other portals |
| **Session Management** | Custom | CSRF token handling and persistent sessions |

### Environment & Configuration

| Technology | Version | Purpose |
|------------|---------|---------|
| **python-dotenv** | ≥1.0.0 | Environment variable management |
| **pytz** | ≥2023.3 | Timezone handling for scheduling |

---

## 📊 Core Features

### 1. Multi-Portal Bid Scraping

**Supported Portals:**

| Portal | URL | Categories |
|--------|-----|------------|
| **GeM** | bidplus.gem.gov.in | All consulting bids |
| **CPPP** | eprocure.gov.in | Central Public Procurement Portal |
| **DPPP** | defproc.gov.in | Defence Public Procurement |

**Capabilities:**

- ✅ CSRF token extraction and session management
- ✅ Multi-page pagination (up to 20 pages, ~200 bids)
- ✅ Keyword-based full-text search
- ✅ Date range filtering (bid end dates)
- ✅ Consulting-only filtering with taxonomy classification
- ✅ Semantic keyword expansion (e.g., "ERP" → "SAP", "Oracle")

---

### 2. AI-Powered Analysis (Gemini Integration)

| Feature | Description |
|---------|-------------|
| **CFS Score** | Consulting Fit Score (0-100) measuring alignment with firm capabilities |
| **Go/No-Go Matrix** | Traffic light indicators (🟢/🟡/🔴) for Eligibility, Timeline, Technical Fit, Strategic Value, Risk Level |
| **Executive Summary** | Structured output with "The Ask", Key Deliverables, Evaluation Criteria |
| **AI Reasoning** | Detailed explanation of why bid fits or doesn't fit firm profile |

**CFS Score Interpretation:**

- **80-100** → Strong Fit → **GO**
- **50-79** → Marginal Fit → **MAYBE**
- **0-49** → Out of Scope → **NO-GO**

---

### 3. Virtual User (SOW Reader Agent)

| Step | Action |
|------|--------|
| PDF Scan | Scans first 30 pages for "Scope of Work" section headers |
| Boundary Detection | AI identifies SOW start/end pages |
| Text Extraction | Extracts text from identified page range |
| AI Summary | Generates structured summary with requirements, quantities, qualifications |

---

### 4. Consulting Taxonomy Classification

Bids are automatically classified into 5 categories:

| Category | Keywords/Examples |
|----------|-------------------|
| **Strategy & Policy** | DPR, Feasibility Study, Vision Document, Roadmap |
| **Tech & Digital** | ERP, Cloud Migration, AI/ML, Cybersecurity, E-Governance |
| **PMU / PMC** | Project Management Unit, Implementation Support, Manpower |
| **Audit & Finance** | Statutory Audit, Due Diligence, Financial Advisory |
| **HR & Capacity** | Training, Capacity Building, Change Management |

---

### 5. Watchlist & Change Monitoring

| Feature | Description |
|---------|-------------|
| **Add/Remove** | One-click watchlist management from dashboard |
| **Update Checking** | Scans watched bids for date changes, corrigenda |
| **Change Logging** | All detected changes logged with timestamps |
| **Alert System** | Notifications for significant changes |

---

### 6. Daily Scrape Results

| Filter | Options |
|--------|---------|
| **Time Range** | 7, 15, 30, 90, 180, 365 days |
| **Manual Trigger** | "Run Now" button for immediate scraping |
| **View Modes** | Cards or Table display |
| **Portal Filter** | Filter by source portal |
| **Category Filter** | Consulting, IT, Defence |

---

### 7. Scheduler (Background Automation)

| Job | Schedule |
|-----|----------|
| **Daily Intelligence Run** | 08:00 AM daily (configurable) |
| **Watchlist Check** | Every 6 hours |

**Output:** JSON digests saved to `digests/` folder.

---

### 8. Analytics Dashboard

| Metric | Description |
|--------|-------------|
| Total Bids Scraped | Count of all bids in database |
| High-Fit Opportunities | Bids with CFS ≥ 80 |
| Pending Analysis | Bids not yet analyzed by AI |
| Category Breakdown | Distribution across consulting categories |

---

### 9. Data Export

| Format | Contents |
|--------|----------|
| **CSV** | Bid Number, Items, Department, Dates, Links |
| **JSON** | Full data including CFS scores, AI reasoning, executive summaries |

---

### 10. Email Notifications

| Feature | Description |
|---------|-------------|
| **Daily Digest** | Automated email with top opportunities |
| **Alert Emails** | Notifications for high-fit bids and changes |
| **Custom Templates** | HTML-formatted professional emails |

---

### 11. User Authentication

| Feature | Description |
|---------|-------------|
| **User Login/Registration** | Secure authentication system |
| **Session Management** | Persistent login sessions |
| **Google OAuth** | Optional Google authentication |

---

## 📁 Project Architecture

```
gem_scraper/
├── app.py                    # Streamlit UI (1607 lines)
├── gem_scraper.py            # Core GeM scraping logic
├── ai_analyzer.py            # Gemini AI integration
├── virtual_agent.py          # PDF reader agent for SOW
├── database.py               # SQLite storage layer
├── config.py                 # Centralized configuration
├── auth.py                   # User authentication
├── email_notifier.py         # Email notification system
├── agent_scheduler.py        # Background job scheduler
├── ad_scorer.py              # Advanced scoring logic
├── ad_taxonomy.py            # Consulting taxonomy definitions
├── ad_config.py              # Advanced configuration
├── pattern_detector.py       # Pattern detection utilities
├── portal_scrapers/          # Multi-portal scraper modules
│   ├── base_scraper.py       # Base scraper class
│   ├── nic_scraper.py        # CPPP/DPPP scraper
│   └── unified_scraper.py    # Unified scraper interface
├── cip_data.db               # SQLite database
├── digests/                  # Daily digest JSON files
├── downloads/                # Downloaded bid PDFs
├── reports/                  # Generated reports
├── .env                      # Environment variables
└── requirements.txt          # Python dependencies
```

---

## 🗄️ Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `bids` | Core bid metadata (number, items, dates, links, source_portal) |
| `ai_analysis` | CFS scores, Go/No-Go matrices, summaries |
| `watchlist` | Bids being monitored |
| `change_log` | Historical changes detected |

### Key Relationships

```
bids.bid_number  ←──→  ai_analysis.bid_number (1:1)
bids.bid_number  ←──→  watchlist.bid_number (1:1)
bids.bid_number  ←──→  change_log.bid_number (1:N)
```

---

## 📡 External APIs

| Source | Endpoint | Method |
|--------|----------|--------|
| **GeM Portal** | `bidplus.gem.gov.in/all-bids-data` | POST |
| **CPPP** | `eprocure.gov.in` | GET |
| **DPPP** | `defproc.gov.in` | GET |
| **Gemini AI** | `generativelanguage.googleapis.com` | POST |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
# Add GOOGLE_API_KEY=your_key to .env file

# 3. Run application
python -m streamlit run app.py

# 4. Access
# Open http://localhost:8501
```

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Gemini AI API key | Yes |
| `SMTP_HOST` | Email server host | No |
| `SMTP_PORT` | Email server port | No |
| `SMTP_USER` | Email username | No |
| `SMTP_PASSWORD` | Email password | No |

---

## 📈 Performance Specifications

| Metric | Value |
|--------|-------|
| Max Pages per Scrape | 20 pages (~200 bids) |
| Scraping Rate Limit | 1 second delay between requests |
| PDF Scan Limit | First 30 pages for SOW detection |
| Database | SQLite (local, ~1MB per 1000 bids) |

---

**Last Updated:** December 2025
