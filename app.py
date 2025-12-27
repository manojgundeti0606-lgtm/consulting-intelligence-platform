import streamlit as st
import pandas as pd
import os
import json
import time
import re
from datetime import datetime, timedelta
from pathlib import Path

from gem_scraper import scrape_bids, download_document, extract_text_from_pdf, extract_hyperlinks_from_pdf
from ai_analyzer import analyze_bid_complete
from database import CIPDatabase
from agent_scheduler import CIPAgent
from config import FIRM_PROFILE, NOTIFICATION_CONFIG
from virtual_agent import BidReaderAgent

# Page config
st.set_page_config(
    page_title="Consulting Intelligence Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern UI Styling - Premium Dark Theme with Glassmorphism
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables */
    :root {
        --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-success: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        --gradient-warning: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --gradient-info: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --card-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Container Background */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Sidebar Items */
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: rgba(255, 255, 255, 0.85);
    }
    
    /* Headers with Gradient */
    h1 {
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    h2 {
        color: #e0e0e0 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid rgba(102, 126, 234, 0.5);
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: #b8b8b8 !important;
        font-weight: 500 !important;
    }
    
    /* Card Styling */
    [data-testid="stExpander"] {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: var(--card-shadow);
        transition: all 0.3s ease;
    }
    
    [data-testid="stExpander"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.45);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    /* Button Styling */
    .stButton > button {
        background: var(--gradient-primary) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Primary Button */
    .stButton > button[kind="primary"] {
        background: var(--gradient-success) !important;
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4);
    }
    
    /* Metrics Styling */
    [data-testid="stMetric"] {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 1.2rem !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    [data-testid="stMetricValue"] {
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: white !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-primary) !important;
        border: none !important;
    }
    
    /* Success/Info/Warning/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(17, 153, 142, 0.2) 0%, rgba(56, 239, 125, 0.2) 100%) !important;
        border: 1px solid rgba(56, 239, 125, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(79, 172, 254, 0.2) 0%, rgba(0, 242, 254, 0.2) 100%) !important;
        border: 1px solid rgba(79, 172, 254, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(240, 147, 251, 0.2) 0%, rgba(245, 87, 108, 0.2) 100%) !important;
        border: 1px solid rgba(245, 87, 108, 0.3) !important;
        border-radius: 12px !important;
    }
    
    /* Dataframe Styling */
    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--glass-border);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: var(--gradient-primary) !important;
        border-radius: 10px;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.5), transparent);
        margin: 1.5rem 0;
    }
    
    /* Score Badge Styling */
    .score-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .score-high {
        background: linear-gradient(135deg, rgba(17, 153, 142, 0.3), rgba(56, 239, 125, 0.3));
        color: #38ef7d;
        border: 1px solid rgba(56, 239, 125, 0.4);
    }
    
    .score-medium {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.3), rgba(255, 152, 0, 0.3));
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.4);
    }
    
    .score-low {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.3), rgba(211, 47, 47, 0.3));
        color: #f44336;
        border: 1px solid rgba(244, 67, 54, 0.4);
    }
    
    /* Recommendation Badges */
    .rec-pursue {
        background: var(--gradient-success);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 8px;
        font-weight: 600;
        display: inline-block;
    }
    
    .rec-evaluate {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 8px;
        font-weight: 600;
        display: inline-block;
    }
    
    .rec-pass {
        background: linear-gradient(135deg, #636363 0%, #434343 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 8px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Popover Styling */
    [data-testid="stPopover"] {
        background: rgba(26, 26, 46, 0.95) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }
    
    /* Radio Buttons Styling */
    [data-testid="stRadio"] > div {
        gap: 0.5rem;
    }
    
    [data-testid="stRadio"] label {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 0.8rem 1rem !important;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    [data-testid="stRadio"] label:hover {
        background: rgba(102, 126, 234, 0.15);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #667eea !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* Animation for cards */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .element-container {
        animation: fadeIn 0.3s ease-out;
    }
</style>
""", unsafe_allow_html=True)

def display_sow_button(bid, key_suffix):
    """Helper to display SOW button and handle logic"""
    bid_num = bid.get('Bid Number') or bid.get('bid_number')
    if st.button("📋 Scope of Work", key=f"sow_{bid_num}_{key_suffix}"):
        with st.spinner("Fetching & Analyzing Document..."):
            doc_link = bid.get('Document Link') or bid.get('document_link')
            doc_path = download_document(doc_link, bid_data=bid)
            
            if doc_path:
                # Use Virtual Agent to summarize
                try:
                    agent = BidReaderAgent(doc_path)
                    summary = agent.summarize_sow()
                    st.success("✅ Analysis Complete")
                    st.info(f"**Scope of Work Summary:**\n\n{summary}")
                except Exception as e:
                    st.error(f"Error analyzing document: {e}")
            else:
                st.error("Failed to download document.")

def display_full_analysis_button(bid, key_suffix):
    """
    Combined SOW extraction + AI Analysis button.
    Stores results in session state for full-width display.
    """
    bid_num = bid.get('Bid Number') or bid.get('bid_number')
    analysis_key = f"analysis_result_{bid_num}"
    
    if st.button("🔍 Full Analysis", key=f"full_analysis_{bid_num}_{key_suffix}", type="primary"):
        # Store that we're running analysis for this bid
        st.session_state[f"running_analysis_{bid_num}"] = True
        st.session_state[analysis_key] = None  # Clear previous
        st.rerun()


def run_and_display_analysis(bid, key_suffix):
    """
    Run analysis and display results in full width.
    Called outside of columns for proper layout.
    """
    bid_num = bid.get('Bid Number') or bid.get('bid_number')
    analysis_key = f"analysis_result_{bid_num}"
    running_key = f"running_analysis_{bid_num}"
    
    # Check if analysis was requested
    if st.session_state.get(running_key):
        with st.container():
            with st.spinner("🔄 Running comprehensive analysis..."):
                doc_link = bid.get('Document Link') or bid.get('document_link')
                
                # Progress display
                progress_container = st.empty()
                progress_container.info("📥 Step 1/3: Downloading document...")
                doc_path = download_document(doc_link, bid_data=bid)
                
                if not doc_path:
                    progress_container.error("❌ Failed to download document.")
                    st.session_state[running_key] = False
                    return
                
                try:
                    progress_container.info("📋 Step 2/3: Extracting Scope of Work...")
                    agent = BidReaderAgent(doc_path)
                    sow_summary = agent.summarize_sow()
                    
                    progress_container.info("🤖 Step 3/3: Running AI analysis...")
                    from ai_analyzer import analyze_bid_complete, analyze_tender_ad_intelligence
                    
                    # Try A&D intelligence analysis
                    try:
                        ad_analysis = analyze_tender_ad_intelligence(bid, sow_text=sow_summary, pdf_path=doc_path)
                        has_ad_analysis = True
                    except Exception:
                        ad_analysis = None
                        has_ad_analysis = False
                    
                    # Standard CFS analysis
                    full_analysis = analyze_bid_complete(bid, sow_text=sow_summary, pdf_path=doc_path)
                    
                    # Save to database
                    st.session_state.db.save_ai_analysis(full_analysis)
                    
                    # Store results
                    st.session_state[analysis_key] = {
                        'sow': sow_summary,
                        'cfs': full_analysis,
                        'ad': ad_analysis,
                        'has_ad': has_ad_analysis,
                        'bid_num': bid_num
                    }
                    
                    progress_container.success("✅ Analysis Complete!")
                    st.session_state[running_key] = False
                    
                except Exception as e:
                    progress_container.error(f"❌ Error: {str(e)}")
                    st.session_state[running_key] = False
                    return
    
    # Display stored results if available
    if st.session_state.get(analysis_key):
        result = st.session_state[analysis_key]
        
        with st.expander(f"📊 Analysis Results: {result['bid_num']}", expanded=True):
            # Create full-width tabbed display
            tab1, tab2, tab3 = st.tabs(["📋 SOW Summary", "🎯 AI Analysis", "📊 A&D Intelligence"])
            
            with tab1:
                st.markdown("### Scope of Work Summary")
                st.markdown(result['sow'])
            
            with tab2:
                st.markdown("### AI Analysis Results")
                
                # CFS Score cards in columns
                cfs = result['cfs'].get('cfs', {})
                score = cfs.get('score', 0)
                verdict = cfs.get('verdict', 'N/A')
                rec = result['cfs'].get('go_no_go', {}).get('overall_recommendation', 'N/A')
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    score_color = "#11998e" if score >= 70 else "#f5a623" if score >= 50 else "#e74c3c"
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; 
                         background: linear-gradient(135deg, {score_color}dd, {score_color}aa); 
                         color: white; border-radius: 16px; margin: 5px;'>
                        <div style='font-size: 2.5rem; font-weight: bold;'>{score}</div>
                        <div style='font-size: 0.95rem; opacity: 0.9;'>CFS Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    rec_color = "#11998e" if rec == "GO" else "#e74c3c" if rec == "NO_GO" else "#f5a623"
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; 
                         background: linear-gradient(135deg, {rec_color}dd, {rec_color}aa); 
                         color: white; border-radius: 16px; margin: 5px;'>
                        <div style='font-size: 1.8rem; font-weight: bold;'>{rec}</div>
                        <div style='font-size: 0.95rem; opacity: 0.9;'>Recommendation</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; 
                         background: linear-gradient(135deg, #667eeadd, #764ba2aa); 
                         color: white; border-radius: 16px; margin: 5px;'>
                        <div style='font-size: 1.4rem; font-weight: bold;'>{verdict}</div>
                        <div style='font-size: 0.95rem; opacity: 0.9;'>Verdict</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Reasoning
                if cfs.get('reasoning'):
                    st.markdown("**💡 AI Reasoning:**")
                    st.info(cfs['reasoning'])
                
                # Executive Summary
                exec_summary = result['cfs'].get('executive_summary', {})
                if exec_summary and isinstance(exec_summary, dict):
                    st.markdown("**📝 Executive Summary:**")
                    if exec_summary.get('the_ask'):
                        st.markdown(f"**The Ask:** {exec_summary['the_ask']}")
                    if exec_summary.get('key_deliverables'):
                        st.markdown("**Key Deliverables:**")
                        for d in exec_summary['key_deliverables']:
                            st.markdown(f"  • {d}")
            
            with tab3:
                if result['has_ad'] and result['ad']:
                    st.markdown("### A&D Intelligence Analysis")
                    
                    ad = result['ad']
                    ad_score = ad.get('a_d_relevance_score', 0)
                    ad_rec = ad.get('recommendation', 'EVALUATE')
                    
                    # Score metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("A&D Score", f"{ad_score:.0f}/100")
                    with col2:
                        st.metric("Confidence", f"{ad.get('confidence', 50):.0f}%")
                    with col3:
                        st.metric("Category", ad.get('a_d_sub_category', 'N/A'))
                    with col4:
                        rec_emoji = "🟢" if ad_rec == "PURSUE" else "🟡" if ad_rec == "EVALUATE" else "🔴"
                        st.metric("Action", f"{rec_emoji} {ad_rec}")
                    
                    st.markdown("---")
                    
                    # Risk Assessment
                    risk = ad.get('risk_assessment', {})
                    if risk:
                        st.markdown("**⚠️ Risk Assessment:**")
                        cols = st.columns(4)
                        risk_items = [
                            ("Implementation", risk.get('implementation_risk', 'N/A')),
                            ("Scope Creep", risk.get('scope_creep_risk', 'N/A')),
                            ("Political", risk.get('political_risk', 'N/A')),
                            ("Win Prob.", risk.get('win_probability', 'N/A'))
                        ]
                        for col, (label, value) in zip(cols, risk_items):
                            with col:
                                color = "#11998e" if value == "Low" else "#f5a623" if value == "Medium" else "#e74c3c"
                                st.markdown(f"**{label}:** <span style='color: {color}'>{value}</span>", unsafe_allow_html=True)
                    
                    # Matched Keywords
                    keywords = ad.get('matched_keywords', [])
                    if keywords:
                        st.markdown("**🏷️ Matched Keywords:**")
                        st.write(", ".join(str(k) for k in keywords[:15]))
                else:
                    st.info("A&D Intelligence analysis not available.")
            
            # Close button
            if st.button("❌ Close Analysis", key=f"close_analysis_{result['bid_num']}_{key_suffix}"):
                st.session_state[f"analysis_result_{result['bid_num']}"] = None
                st.rerun()


def extract_links_from_pdf_file(pdf_path):
    """Extract all URLs/links from a PDF file using PyMuPDF (most reliable method)"""
    import fitz  # PyMuPDF
    links = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            
            # Method 1: Get embedded hyperlinks (most reliable)
            page_links = page.get_links()
            for link in page_links:
                if 'uri' in link:
                    links.append({
                        'url': link['uri'],
                        'page': page_num + 1,
                        'type': 'embedded'
                    })
            
            # Method 2: Also extract text-based URLs using regex
            text = page.get_text()
            url_patterns = [
                r'https?://[^\s<>"{}|\\^`\[\]]+',
                r'www\.[^\s<>"{}|\\^`\[\]]+',
            ]
            for pattern in url_patterns:
                found_urls = re.findall(pattern, text)
                for url in found_urls:
                    url = url.rstrip('.,;:)')
                    links.append({
                        'url': url,
                        'page': page_num + 1,
                        'type': 'text'
                    })
        
        doc.close()
    except Exception as e:
        print(f"Error extracting links: {e}")
    
    # Remove duplicates (prefer embedded over text)
    seen = set()
    unique_links = []
    for link in links:
        if link['url'] not in seen:
            seen.add(link['url'])
            unique_links.append(link)
    
    return unique_links

def display_links_button(bid, key_suffix):
    """Helper to display extracted links from bid document"""
    bid_num = bid.get('Bid Number') or bid.get('bid_number')
    
    with st.popover("🔗 View Links"):
        # Try to find the PDF file - only match actual .pdf files
        downloads_dir = Path("downloads")
        all_matches = list(downloads_dir.glob(f"*{bid_num}*.pdf")) + list(downloads_dir.glob(f"**/*{bid_num}*.pdf"))
        # Filter to only actual files (not directories)
        pdf_files = [f for f in all_matches if f.is_file() and f.suffix.lower() == '.pdf']
        
        if pdf_files:
            links = extract_links_from_pdf_file(pdf_files[0])
            if links:
                st.markdown(f"**Found {len(links)} links:**")
                for link in links[:15]:  # Limit to 15 links
                    url = link['url']
                    display_url = url[:60] + "..." if len(url) > 60 else url
                    st.markdown(f"- [Page {link['page']}] [{display_url}]({url})")
                if len(links) > 15:
                    st.caption(f"... and {len(links) - 15} more links")
            else:
                st.info("No links found in document")
        else:
            # Try to download first
            st.info("Document not downloaded yet. Click 'View Document' first.")
            doc_link = bid.get('Document Link') or bid.get('document_link')
            if doc_link:
                if st.button("📥 Download & Extract Links", key=f"dl_links_{bid_num}_{key_suffix}"):
                    with st.spinner("Downloading..."):
                        doc_path = download_document(doc_link, bid_data=bid)
                        if doc_path:
                            links = extract_links_from_pdf_file(doc_path)
                            if links:
                                st.markdown(f"**Found {len(links)} links:**")
                                for link in links[:15]:
                                    url = link['url']
                                    display_url = url[:60] + "..." if len(url) > 60 else url
                                    st.markdown(f"- [Page {link['page']}] [{display_url}]({url})")
                            else:
                                st.info("No links found in document")

# Initialize database
if 'db' not in st.session_state:
    st.session_state.db = CIPDatabase()
elif not hasattr(st.session_state.db, 'get_recent_bids_with_analysis'):
    # Force reload if method is missing (stale object)
    st.session_state.db = CIPDatabase()

# Initialize agent
if 'agent' not in st.session_state:
    st.session_state.agent = CIPAgent()

# Initialize results if empty
if 'current_results' not in st.session_state:
    st.session_state['current_results'] = st.session_state.db.get_recent_bids_with_analysis(limit=20)

# Sidebar
with st.sidebar:
    st.title("🎯 CIP")
    st.markdown("**Consulting Intelligence Platform**")
    st.divider()
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["🔍 Intelligence Dashboard", "📅 Daily Scrape", "⭐ Watchlist", "📊 Analytics", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Firm Profile Summary
    with st.expander("📋 Firm Profile"):
        st.markdown(f"**{FIRM_PROFILE['name']}**")
        st.caption(f"Focus Areas: {len(FIRM_PROFILE['expertise_areas'])} domains")
        st.caption(f"Min CFS Score: {NOTIFICATION_CONFIG['min_cfs_score']}")

# Page 1: Intelligence Dashboard
if page == "🔍 Intelligence Dashboard":
    st.title("🔍 Intelligence Dashboard")
    st.caption("AI-powered consulting opportunity discovery")
    
    # Search Section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Search & Filter")
    
    with col2:
        if st.button("▶️ Run Intelligence Now", type="primary", use_container_width=True):
            with st.spinner("Running AI-powered analysis..."):
                count = st.session_state.agent.run_now('daily_intelligence')
                
                # Fetch latest results
                limit = count if count > 0 else 20
                latest_bids = st.session_state.db.get_recent_bids_with_analysis(limit=limit)
                st.session_state['current_results'] = latest_bids
                
                st.success(f"✅ Found {count} high-fit opportunities!")
                st.rerun()
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        keywords = st.text_input(
            "Keywords",
            placeholder="e.g., Digital Transformation, ERP, Cloud",
            help="Leave empty for broad search"
        )
    
    with col2:
        from_date = st.date_input(
            "From Date",
            value=datetime.now() - timedelta(days=30)
        )
    
    with col3:
        to_date = st.date_input(
            "To Date",
            value=datetime.now() + timedelta(days=90)
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2, col3 = st.columns(3)
        with col1:
            max_pages = st.slider("Max Pages", 1, 20, 10)
        with col2:
            consulting_only = st.checkbox("Consulting Only", value=True)
        with col3:
            run_ai_analysis = st.checkbox("Run AI Analysis", value=True)
    
    # Search button
    if st.button("🔎 Search Bids", type="secondary"):
        with st.spinner("Scraping and analyzing..."):
            # Scrape bids
            bids = scrape_bids(
                keywords=keywords,
                from_date=from_date.strftime('%Y-%m-%d') if from_date else "",
                to_date=to_date.strftime('%Y-%m-%d') if to_date else "",
                max_pages=max_pages,
                consulting_only=consulting_only
            )
            
            if bids:
                st.success(f"Found {len(bids)} bids!")
                
                # Save to database and run AI analysis
                analyzed_bids = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, bid in enumerate(bids):
                    status_text.text(f"Analyzing {i+1}/{len(bids)}: {bid['Bid Number']}")
                    
                    # Save bid
                    st.session_state.db.save_bid(bid)
                    
                    # Run AI analysis if enabled
                    if run_ai_analysis:
                        analysis = analyze_bid_complete(bid)
                        st.session_state.db.save_ai_analysis(analysis)
                        
                        analyzed_bids.append({
                            **bid,
                            'CFS Score': analysis['cfs']['score'],
                            'Verdict': analysis['cfs']['verdict'],
                            'Recommendation': analysis['go_no_go']['overall_recommendation']
                        })
                    else:
                        analyzed_bids.append(bid)
                    
                    progress_bar.progress((i + 1) / len(bids))
                
                status_text.text("✅ Analysis complete!")
                st.session_state['current_results'] = analyzed_bids
            else:
                st.warning("No bids found")
    
    st.divider()
    
    # Results Section
    if 'current_results' in st.session_state and st.session_state['current_results']:
        st.subheader("📊 Results")
        
        results = st.session_state['current_results']
        
        # Filter by CFS score
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            min_score = st.slider("Minimum CFS Score", 0, 100, 0) # Default to 0 to show all
        with col2:
            category_filter = st.multiselect(
                "Category",
                options=list(set([r.get('Category', 'Unknown') for r in results])),
                default=None
            )
        
        # Filter results
        filtered_results = results
        if 'CFS Score' in results[0]:
            filtered_results = [r for r in results if r.get('CFS Score', 0) >= min_score]
        if category_filter:
            filtered_results = [r for r in filtered_results if r.get('Category') in category_filter]
        
        st.caption(f"Showing {len(filtered_results)} of {len(results)} bids")
        
        # Display as cards or table
        view_mode = st.radio("View", ["Cards", "Table"], horizontal=True, label_visibility="collapsed")
        
        if view_mode == "Cards":
            for i, bid in enumerate(filtered_results):
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        # Bid number and category
                        st.markdown(f"### {bid['Bid Number']}")
                        if 'Category' in bid:
                            st.caption(f"📂 {bid['Category']}")
                    
                    with col2:
                        # CFS Score badge
                        if 'CFS Score' in bid:
                            score = bid['CFS Score']
                            verdict = bid.get('Verdict', '')
                            
                            if verdict == 'Analysis Failed':
                                st.markdown(f"<div style='text-align: center; padding: 10px; background-color: gray; color: white; border-radius: 5px; font-weight: bold;'>⚠️ Failed</div>", unsafe_allow_html=True)
                            else:
                                color = "green" if score >= 80 else "orange" if score >= 50 else "red"
                                st.markdown(f"<div style='text-align: center; padding: 10px; background-color: {color}; color: white; border-radius: 5px; font-weight: bold;'>CFS: {score}</div>", unsafe_allow_html=True)
                    
                    # Items and Department
                    st.markdown(f"**Items:** {bid.get('Items', 'N/A')}")
                    st.markdown(f"**Department:** {bid.get('Department', 'N/A')}")
                    
                    # Dates
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"📅 End: {bid.get('End Date', 'N/A')}")
                    with col2:
                        if 'Verdict' in bid:
                            st.caption(f"🎯 {bid['Verdict']}")
                    with col3:
                        if 'Recommendation' in bid:
                            rec = bid['Recommendation']
                            icon = "✅" if rec == "GO" else "⚠️" if rec == "MAYBE" else "❌"
                            st.caption(f"{icon} {rec}")
                    
                    # Actions
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button(f"⭐ Watchlist", key=f"watch_{bid['Bid Number']}_{i}"):
                            st.session_state.db.add_to_watchlist(bid['Bid Number'])
                            st.success("Added!")
                    with col2:
                        st.link_button("📄 Document", bid.get('Document Link', '#'))
                    with col3:
                        display_links_button(bid, f"dashboard_{i}")
                    with col4:
                        display_full_analysis_button(bid, f"dashboard_{i}")
                
                # Display analysis results in full width (outside columns)
                run_and_display_analysis(bid, f"dashboard_{i}")
        
        else:  # Table view
            df = pd.DataFrame(filtered_results)
            # Reorder columns
            column_order = ['Bid Number', 'Category', 'CFS Score', 'Verdict', 
                           'Items', 'Department', 'End Date', 'Recommendation']
            display_columns = [col for col in column_order if col in df.columns]
            st.dataframe(df[display_columns], use_container_width=True, hide_index=True)
        
        # Export options
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            # CSV export
            df = pd.DataFrame(filtered_results)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name=f"cip_results_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2:
            # JSON export with AI metadata
            json_data = json.dumps(filtered_results, indent=2, ensure_ascii=False)
            st.download_button(
                "📥 Download JSON (with AI data)",
                data=json_data,
                file_name=f"cip_results_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

# Page 1.5: Daily Scrape Results
elif page == "📅 Daily Scrape":
    st.title("📅 Daily Scrape Results")
    st.caption("Automated intelligence gathered by the agent")
    
    st.title("📅 Daily Scrape Results")
    st.caption("Automated intelligence gathered by the agent")
    
    # Run Now Button
    col1, col2 = st.columns([3, 1])
    with col1:
        view_mode = st.radio(
            "View Mode", 
            ["📁 Daily Digests (Files)", "🗄️ Historical Data (DB)"], 
            horizontal=True,
            label_visibility="collapsed"
        )
    with col2:
        if st.button("▶️ Run Scrape Now", type="primary", use_container_width=True):
            with st.spinner("Running agent... this may take a while"):
                count = st.session_state.agent.run_now('daily_intelligence')
                st.success(f"Run complete! Found {count} high-fit opportunities.")
                time.sleep(2)
                st.rerun()
    
    st.divider()
    
    if view_mode == "📁 Daily Digests (Files)":
        digest_dir = NOTIFICATION_CONFIG['digest_path']
        if not os.path.exists(digest_dir):
            st.info("No daily digests found. The agent hasn't run yet.")
        else:
            # Get list of digests
            digests = [f for f in os.listdir(digest_dir) if f.endswith('.json')]
            if not digests:
                st.info("No daily digests found.")
            else:
                digests.sort(reverse=True)
                
                # Date selector
                selected_digest = st.selectbox(
                    "Select Date",
                    digests,
                    format_func=lambda x: x.replace('digest_', '').replace('.json', '')
                )
                
                # Load data
                with open(os.path.join(digest_dir, selected_digest), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Summary stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Opportunities", data.get('total_opportunities', 0))
                with col2:
                    st.metric("Generated At", data.get('generated_at', 'N/A')[:16].replace('T', ' '))
                with col3:
                    st.metric("Firm Profile", data.get('firm_name', 'Unknown'))
                
                st.subheader("Opportunities")
                
                opportunities = data.get('opportunities', [])
                if not opportunities:
                    st.info("No opportunities found in this digest.")
                else:
                    for bid in opportunities:
                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.markdown(f"### {bid['bid_number']}")
                                st.caption(f"📂 {bid['category']}")
                                st.markdown(f"**Items:** {bid['items']}")
                                st.markdown(f"**Department:** {bid['department']}")
                            
                            with col2:
                                # CFS Score
                                score = bid['cfs_score']
                                color = "green" if score >= 80 else "orange" if score >= 50 else "red"
                                st.markdown(f"<div style='text-align: center; padding: 10px; background-color: {color}; color: white; border-radius: 5px; font-weight: bold;'>CFS: {score}</div>", unsafe_allow_html=True)
                            
                            # Executive Summary
                            if 'executive_summary' in bid:
                                with st.expander("📄 Executive Summary", expanded=True):
                                    summary = bid['executive_summary']
                                    st.markdown(f"**The Ask:** {summary.get('the_ask', 'N/A')}")
                                    st.markdown("**Key Deliverables:**")
                                    for d in summary.get('key_deliverables', []):
                                        st.markdown(f"- {d}")
                            
                            # Actions
                            col1, col2, col3, col4, col5 = st.columns(5)
                            with col1:
                                 # Re-use existing DB logic for watchlist if needed
                                 if st.button(f"⭐ Add to Watchlist", key=f"daily_watch_{bid['bid_number']}"):
                                    st.session_state.db.add_to_watchlist(bid['bid_number'])
                                    st.success("Added!")
                            with col2:
                                st.link_button("📄 View Document", bid.get('document_link', '#'))
                            with col3:
                                display_sow_button(bid, f"daily_{bid['bid_number']}")
                            with col4:
                                display_links_button(bid, f"daily_{bid['bid_number']}")
                            with col5:
                                updated_rec = bid.get('recommendation', 'N/A')
                                st.caption(f"Rec: {updated_rec}")

    else:  # Historical Data (DB)
        col1, col2 = st.columns([1, 3])
        with col1:
            period = st.selectbox(
                "Time Period",
                ["Last 7 Days", "Last 15 Days", "Last 1 Month", "Last 3 Months", "Last 6 Months", "Last 1 Year"]
            )
            
            # Map selection to days
            days_map = {
                "Last 7 Days": 7,
                "Last 15 Days": 15,
                "Last 1 Month": 30,
                "Last 3 Months": 90,
                "Last 6 Months": 180,
                "Last 1 Year": 365
            }
            days = days_map[period]
            
        with col2:
            st.info(f"Showing automated analysis results from the last {days} days.")
            
        results = st.session_state.db.get_bids_in_period(days)
        
        if not results:
            st.warning("No data found for this period.")
        else:
            st.success(f"Found {len(results)} bids.")
            
            for i, bid in enumerate(results):
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"### {bid['Bid Number']}")
                        st.caption(f"📂 {bid.get('Category', 'Unknown')}")
                        st.markdown(f"**Items:** {bid.get('Items', 'N/A')}")
                        st.markdown(f"**Department:** {bid.get('Department', 'N/A')}")
                    
                    with col2:
                        # CFS Score
                        if 'CFS Score' in bid:
                            score = bid['CFS Score']
                            color = "green" if score >= 80 else "orange" if score >= 50 else "red"
                            st.markdown(f"<div style='text-align: center; padding: 10px; background-color: {color}; color: white; border-radius: 5px; font-weight: bold;'>CFS: {score}</div>", unsafe_allow_html=True)
                    
                    # Executive Summary
                    if 'executive_summary' in bid:
                        with st.expander("📄 Executive Summary", expanded=False): # Default collapsed to save space
                            summary = bid['executive_summary']
                            st.markdown(f"**The Ask:** {summary.get('the_ask', 'N/A')}")
                            st.markdown("**Key Deliverables:**")
                            for d in summary.get('key_deliverables', []):
                                st.markdown(f"- {d}")
                    
                    # Actions
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                         if st.button(f"⭐ Add to Watchlist", key=f"hist_watch_{bid['Bid Number']}_{i}"):
                            st.session_state.db.add_to_watchlist(bid['Bid Number'])
                            st.success("Added!")
                    with col2:
                        st.link_button("📄 View Document", bid.get('Document Link', '#'))
                    with col3:
                        display_sow_button(bid, f"hist_{i}")
                    with col4:
                        display_links_button(bid, f"hist_{i}")
                    with col5:
                         if 'Recommendation' in bid:
                            updated_rec = bid['Recommendation']
                            st.caption(f"Rec: {updated_rec}")

# Page 2: Watchlist
elif page == "⭐ Watchlist":
    st.title("⭐ Watchlist")
    st.caption("Track important bids and get change alerts")
    
    watchlist = st.session_state.db.get_watchlist()
    
    if not watchlist:
        st.info("📌 Your watchlist is empty. Add bids from the Intelligence Dashboard!")
    else:
        st.success(f"Monitoring {len(watchlist)} bids")
        
        for bid_number in watchlist:
            bid_data = st.session_state.db.get_bid_with_analysis(bid_number)
            
            if bid_data:
                with st.container(border=True):
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        st.markdown(f"### {bid_data['bid_number']}")
                        st.caption(f"📂 {bid_data.get('category', 'Unknown')}")
                        st.markdown(f"**Items:** {bid_data.get('items', 'N/A')}")
                    
                    with col2:
                        if st.button("🗑️ Remove", key=f"remove_{bid_number}"):
                            st.session_state.db.remove_from_watchlist(bid_number)
                            st.rerun()
        
        if st.button("🔄 Check for Updates", type="primary"):
            with st.spinner("Checking watchlist..."):
                st.session_state.agent.monitor_watchlist()
                st.success("Watchlist checked!")

# Page 3: Analytics
elif page == "📊 Analytics":
    st.title("📊 Analytics & Insights")
    st.caption("Trends and statistics from your intelligence gathering")
    
    # Get all bids from database
    all_bids = st.session_state.db.get_all_bids(limit=500)
    
    if not all_bids:
        st.info("No data yet. Run intelligence gathering to see analytics.")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bids", len(all_bids))
        with col2:
            categories = [b.get('category') for b in all_bids if b.get('category')]
            st.metric("Categories", len(set(categories)))
        with col3:
            watchlist_count = len(st.session_state.db.get_watchlist())
            st.metric("Watchlist", watchlist_count)
        with col4:
            # Count bids added today
            today_bids = [b for b in all_bids if b.get('last_updated', '').startswith(datetime.now().strftime('%Y-%m-%d'))]
            st.metric("Added Today", len(today_bids))
        
        st.divider()
        
        # Category distribution
        if categories:
            st.subheader("Bids by Category")
            category_counts = pd.Series(categories).value_counts()
            st.bar_chart(category_counts)

# Page 4: Settings
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["Firm Profile", "AI Configuration", "Scheduler"])
    
    with tab1:
        st.subheader("Firm Profile")
        st.info("Configure your firm's expertise areas and preferences")
        
        st.text_area(
            "Expertise Areas",
            value=", ".join(FIRM_PROFILE['expertise_areas']),
            height=150,
            disabled=True,
            help="Edit config.py to modify"
        )
        
        st.number_input(
            "Minimum Bid Value (INR)",
            value=FIRM_PROFILE['turnover_threshold'],
            disabled=True
        )
    
    with tab2:
        st.subheader("AI Configuration")
        st.info("AI analysis is powered by Gemini 2.0 Flash")
        
        if os.getenv('GOOGLE_API_KEY'):
            st.success("✅ API Key configured")
        else:
            st.error("❌ API Key not found")
        
        st.number_input(
            "Minimum CFS Score for Digest",
            value=NOTIFICATION_CONFIG['min_cfs_score'],
            disabled=True
        )
    
    with tab3:
        st.subheader("Agent Scheduler")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.agent.is_running:
                st.success("✅ Scheduler is running")
                if st.button("⏸️ Stop Scheduler"):
                    st.session_state.agent.stop_scheduler()
                    st.rerun()
            else:
                st.info("⏸️ Scheduler is stopped")
                if st.button("▶️ Start Scheduler"):
                    st.session_state.agent.start_scheduler()
                    st.rerun()
        
        with col2:
            st.info(f"Daily Run: 08:00 AM\nWatchlist Check: Every 6 hours")
        
        st.divider()
        
        # View recent digests
        st.subheader("Recent Digests")
        digest_dir = NOTIFICATION_CONFIG['digest_path']
        if os.path.exists(digest_dir):
            digests = [f for f in os.listdir(digest_dir) if f.endswith('.json')]
            if digests:
                for digest in sorted(digests, reverse=True)[:5]:
                    with st.expander(digest):
                        with open(os.path.join(digest_dir, digest), 'r') as f:
                            data = json.load(f)
                            st.json(data)
            else:
                st.info("No digests yet")
        else:
            st.info("No digests yet")
