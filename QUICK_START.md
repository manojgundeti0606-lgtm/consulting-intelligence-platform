# Consulting Intelligence Platform - Quick Start Guide

## 🚀 Getting Started

The CIP is now running at: **<http://localhost:8501>**

---

## 📋 First Time Setup

### 1. Verify Configuration

- ✅ API Key configured (Gemini 2.0 Flash)
- ✅ EY Consulting profile loaded
- ✅ Consulting taxonomy (5 categories)
- ✅ All dependencies installed

### 2. Understanding the Interface

**Navigation Sidebar:**

- 🔍 Intelligence Dashboard - Main scraping & analysis
- ⭐ Watchlist - Monitor important bids
- 📊 Analytics - Trends and statistics
- ⚙️ Settings - Configuration & scheduler

---

## 🎯 Quick Workflows

### Workflow 1: Find Consulting Opportunities

1. **Go to Intelligence Dashboard**
2. **Click "▶️ Run Intelligence Now"**
   - Scrapes 10 pages (~100 bids)
   - Filters for consulting-only  
   - Runs AI analysis on each
   - Takes ~6 minutes
3. **Review Results**
   - See CFS scores (color-coded badges)
   - Green (80+) = Strong Fit
   - Orange (50-79) = Marginal Fit
   - Red (<50) = Out of Scope
4. **Expand AI Analysis**
   - Click "🤖 AI Analysis" on any bid
   - Read reasoning, deliverables, evaluation criteria

### Workflow 2: Custom Search

1. **Enter Keywords**: "Digital Transformation", "ERP", "Cloud", etc.
2. **Set Date Range**: From/To dates
3. **Advanced Options**:
   - Max Pages: 1-20 (default: 10)
   - Consulting Only: ✅ (filters goods procurement)
   - Run AI Analysis: ✅ (CFS + Go/No-Go)
4. **Click "🔎 Search Bids"**

### Workflow 3: Monitor Important Bids

1. **From Dashboard**: Click "⭐ Add to Watchlist" on any bid
2. **Go to Watchlist Page**
3. **Click "🔄 Check for Updates"**
   - Checks for date changes, corrigenda
   - Logs changes to database
4. **View Changes** in Settings → Recent Digests

### Workflow 4: Enable Automation

1. **Go to Settings → Scheduler**
2. **Click "▶️ Start Scheduler"**
   - Daily run at 08:00 AM
   - Watchlist check every 6 hours
3. **View Digests**:
   - Saved to `digests/` folder
   - Format: `digest_2024-12-04.json`
   - Contains only high-fit bids (CFS ≥ 50)

---

## 📊 Understanding CFS Scores

### Consulting Fit Score (CFS) - 0 to 100

#### 80-100 (Strong Fit)

- Core EY expertise (Digital Transformation, Strategy, Public Sector)
- High strategic value
- Recommended: **GO**

#### 50-79 (Marginal Fit)

- Some alignment with EY capabilities
- Worth considering
- Recommended: **MAYBE** (manual review)

#### 0-49 (Out of Scope)

- Goods procurement
- Non-consulting work
- Outside EY's domains
- Recommended: **NO-GO**

---

## 🔍 Consulting Taxonomy Categories

When consulting_only=True, bids are filtered by these categories:

1. **Strategy & Policy**
   - DPR, Feasibility Studies, Vision Documents
   - Policy Formulation, Strategic Planning

2. **Tech & Digital**
   - ERP, Cloud Migration, Cybersecurity
   - E-Governance, IT Modernization, AI/ML

3. **PMU / PMC**
   - Project Management Units
   - Manpower Support, Implementation Support

4. **Audit & Finance**
   - Statutory Audit, Due Diligence
   - Financial Advisory, Transaction Advisory

5. **HR & Capacity**
   - Training, Capacity Building
   - Change Management, Talent Development

---

## 💡 Pro Tips

### Maximize AI Analysis Quality

✅ **DO:**

- Use specific keywords ("Cloud Migration" vs. "IT")
- Enable AI analysis for accurate CFS scores
- Review "Reasoning" in AI Analysis popover
- Export JSON to keep AI metadata

❌ **DON'T:**

- Disable "Consulting Only" unless you want ALL bids
- Ignore Yellow/Red CFS scores (they're filtered for a reason)
- Run > 20 pages at once (takes ~20 min)

### Export Data

#### CSV Export

- Good for Excel analysis
- No AI metadata (just bid details)

#### JSON Export

- Includes CFS scores, verdicts, recommendations
- Ready for CRM integration (Salesforce, HubSpot)
- Full executive summaries

### Scheduler Best Practices

#### When to Enable

- You want automated daily intelligence
- You have 10+ bids on watchlist
- You trust the system (after testing manually)

#### When to Keep Manual

- Still testing/validating
- Want full control over searches
- Running ad-hoc analysis

---

## 🗂️ File Locations

### Documents

- **Structured folders**: `downloads/{Year}/{Month}/{Bid_Number}/`
- **Smart naming**: `GEM/2024/123_MoHUA_SmartCity.pdf`

### Digests

- **Location**: `digests/`
- **Daily**: `digest_2024-12-04.json`
- **Changes**: `changes_2024-12-04_14-30.json`

### Database

- **File**: `cip_data.db` (SQLite)
- **Tables**: bids, ai_analysis, watchlist, change_log

---

## 🧪 Testing Your Setup

### Quick Test (5 minutes)

1. **Dashboard** → "Run Intelligence Now"
2. Wait for analysis to complete
3. Check if you see:
   - ✅ Bids with CFS scores
   - ✅ Categories (Strategy & Policy, Tech & Digital, etc.)
   - ✅ AI Analysis popovers work
4. Add 1-2 bids to watchlist
5. Go to **Analytics** - see statistics
6. Go to **Watchlist** - see your saved bids

### Verify AI Analysis

1. Find a bid with high CFS (80+)
2. Click "🤖 AI Analysis"
3. Check:
   - ✅ Reasoning makes sense
   - ✅ "The Ask" is accurate
   - ✅ Deliverables are relevant
   - ✅ Recommendation (GO/MAYBE/NO-GO) is logical

---

## ⚠️ Troubleshooting

### "Analysis Failed" or Score = 0

**Cause**: Gemini API issue
**Fix**:

1. Check `.env` file has correct API key
2. Verify key is active in Google AI Studio
3. Check internet connection

### No Bids Found

**Cause**: Filters too restrictive or taxonomy excluding everything
**Fix**:

1. Try without keywords
2. Widen date range
3. Set `consulting_only=False` temporarily to see ALL bids

### Scheduler Not Running

**Cause**: Process stopped
**Fix**:

1. Settings → Scheduler → "▶️ Start Scheduler"
2. Keep Streamlit app running (don't close terminal)

---

## 📞 Next Steps

1. ✅ **Test the system** with "Run Intelligence Now"
2. ✅ **Review CFS scores** and validate AI analysis
3. ✅ **Export sample data** (JSON) to see structure
4. ✅ **Enable scheduler** when confident
5. ✅ **Check digests daily** in `digests/` folder

---

## 🎯 Success Checklist

Before going to production:

- [ ] Ran "Intelligence Now" successfully
- [ ] Verified CFS scores make sense
- [ ] Reviewed AI reasoning for accuracy
- [ ] Added bids to watchlist
- [ ] Exported JSON with AI metadata
- [ ] Tested scheduler (optional)
- [ ] Reviewed daily digest format

**You're all set!** 🚀

The Consulting Intelligence Platform is fully operational and ready to find high-value consulting opportunities for EY.
