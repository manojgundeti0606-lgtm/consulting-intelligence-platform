import streamlit as st
import pandas as pd
import os
import json
import time
import re
from datetime import datetime, timedelta
from pathlib import Path

from gem_scraper import download_document, extract_text_from_pdf, extract_hyperlinks_from_pdf
from portal_scrapers import UnifiedScraper, PortalType
from ai_analyzer import analyze_bid_complete
from database import CIPDatabase
from agent_scheduler import CIPAgent
from config import FIRM_PROFILE, NOTIFICATION_CONFIG, CONSULTING_TAXONOMY, KEYWORD_EXPANSIONS, SCRAPING_CONFIG, ALL_DEFENCE_ORGANIZATIONS, DEFENCE_ORG_KEYWORDS
from virtual_agent import BidReaderAgent
from auth import AuthManager, init_session, is_logged_in, is_admin, get_current_user, login_user, logout_user
from email_notifier import send_email_digest

# Team Recipients
# TEAM_EMAILS is now managed via database, falling back to config if needed during migration
TEAM_EMAILS_DEPRECATED = NOTIFICATION_CONFIG.get('team_emails', [])

def get_team_emails():
    """Fetch team emails from DB or config"""
    try:
        if 'db' in st.session_state:
            recipients = st.session_state.db.get_all_recipients()
            if recipients:
                return [r['email'] for r in recipients]
    except Exception:
        pass  # Database not available or no recipients yet
    return TEAM_EMAILS_DEPRECATED

def trigger_team_email(bids_list, source_name="Report"):
    """
    Helper to adapt flat bid list to nested structure and send email.
    """
    if not bids_list:
        st.warning("No bids to email.")
        return

    # Adapt flat structure to nested expected by email_notifier
    # Flat: { ..., 'CFS Score': ..., 'Verdict': ..., 'Recommendation': ... }
    # Nested: { 'bid': {...}, 'analysis': { 'cfs': {...}, 'go_no_go': {...} } }
    
    adapted_bids = []
    for bid in bids_list:
        # Reconstruct analysis dict from flat fields if present
        cfs = {
            'score': bid.get('CFS Score') or 0,
            'verdict': bid.get('Verdict', 'N/A'),
            'reasoning': bid.get('Reasoning', 'N/A') # Assuming Reasoning might be flattened
        }
        go_no_go = {
            'overall_recommendation': bid.get('Recommendation', 'N/A')
        }
        # If original analysis logic was full, we might want to fetch full object from DB
        # But for now, we reconstruct enough for the email report
        
        # Try to get full details from DB if possible for better report
        full_analysis = {}
        cached = None  # Initialize here so it's accessible later
        if 'Bid Number' in bid:
            try:
                cached = st.session_state.db.get_bid_with_analysis(bid['Bid Number'])
                if cached:
                    full_analysis = cached
            except Exception:
                pass  # Could not fetch cached analysis
        
        if not full_analysis:
            full_analysis = {
                'cfs': cfs,
                'go_no_go': go_no_go,
                'executive_summary': bid.get('executive_summary', {})
            }

        # Get sow_summary from cached analysis (DB) or from bid
        sow_summary = ''
        if cached:
            sow_summary = cached.get('sow_summary') or bid.get('sow_summary', '')
        else:
            sow_summary = bid.get('sow_summary', '')

        adapted_bids.append({
            'bid': bid,
            'analysis': full_analysis,
            'sow_summary': sow_summary
        })

    recipients = get_team_emails()
    with st.spinner(f"Sending email to team ({len(recipients)} recipients)..."):
        subject = f"📊 {source_name}: {len(bids_list)} Bids Found - {datetime.now().strftime('%d %b %Y')}"
        success = send_email_digest(adapted_bids, recipient_emails=recipients, subject=subject)
        
        if success:
            st.toast(f"✅ Email sent to team!", icon="📧")
            st.success(f"Report sent to: {', '.join(recipients)}")
        else:
            st.error("Failed to send email. Check logs.")

# Page config
st.set_page_config(
    page_title="Consulting Intelligence Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern UI Styling - Professional Yellow & Dark Theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables - EY Color Palette */
    :root {
        --primary-dark: #333333;
        --primary-yellow: #ffe600;
        --primary-white: #ffffff;
        --border-gray: #cccccc;
        --text-secondary: #999999;
        --gradient-primary: linear-gradient(135deg, #ffe600 0%, #ffcc00 100%);
        --gradient-dark: linear-gradient(135deg, #333333 0%, #1a1a1a 100%);
        --glass-bg: rgba(255, 255, 255, 0.95);
        --glass-border: #cccccc;
        --card-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Container Background */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
        background: var(--primary-white);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: var(--gradient-dark);
        border-right: 1px solid var(--border-gray);
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Sidebar Items */
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: rgba(255, 255, 255, 0.85);
    }
    
    /* Headers with Yellow Accent */
    h1 {
        color: var(--primary-dark) !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
        border-left: 4px solid var(--primary-yellow);
        padding-left: 15px;
    }
    
    h2 {
        color: var(--primary-dark) !important;
        font-weight: 600 !important;
        border-bottom: 3px solid var(--primary-yellow);
        padding-bottom: 0.5rem;
    }
    
    h3 {
        color: var(--primary-dark) !important;
        font-weight: 500 !important;
    }
    
    /* Card Styling */
    [data-testid="stExpander"] {
        background: var(--primary-white);
        border: 1px solid var(--border-gray);
        border-radius: 12px;
        box-shadow: var(--card-shadow);
        transition: all 0.3s ease;
    }
    
    [data-testid="stExpander"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        border-left: 4px solid var(--primary-yellow);
    }
    
    /* Button Styling */
    .stButton > button {
        background: var(--gradient-dark) !important;
        color: var(--primary-white) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 10px rgba(51, 51, 51, 0.3);
    }
    
    .stButton > button:hover {
        background: var(--primary-dark) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(51, 51, 51, 0.4) !important;
    }
    
    /* Primary Button - Yellow */
    .stButton > button[kind="primary"] {
        background: var(--gradient-primary) !important;
        color: var(--primary-dark) !important;
        box-shadow: 0 2px 10px rgba(255, 230, 0, 0.4);
    }
    
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 20px rgba(255, 230, 0, 0.6) !important;
    }
    
    /* Metrics Styling */
    [data-testid="stMetric"] {
        background: var(--primary-white);
        border: 1px solid var(--border-gray);
        border-left: 4px solid var(--primary-yellow);
        border-radius: 12px;
        padding: 1.2rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    [data-testid="stMetricValue"] {
        color: var(--primary-dark) !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {
        background: var(--primary-white) !important;
        border: 1px solid var(--border-gray) !important;
        border-radius: 8px !important;
        color: var(--primary-dark) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-yellow) !important;
        box-shadow: 0 0 0 2px rgba(255, 230, 0, 0.3) !important;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--primary-white);
        border: 1px solid var(--border-gray);
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        transition: all 0.3s ease;
        color: var(--primary-dark);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-yellow) !important;
        border: 1px solid var(--primary-yellow) !important;
        color: var(--primary-dark) !important;
        font-weight: 600;
    }
    
    /* Success/Info/Warning/Error Messages */
    .stSuccess {
        background: rgba(40, 167, 69, 0.1) !important;
        border-left: 4px solid #28a745 !important;
        border-radius: 8px !important;
        color: var(--primary-dark) !important;
    }
    
    .stInfo {
        background: rgba(255, 230, 0, 0.1) !important;
        border-left: 4px solid var(--primary-yellow) !important;
        border-radius: 8px !important;
        color: var(--primary-dark) !important;
    }
    
    .stWarning {
        background: rgba(255, 193, 7, 0.1) !important;
        border-left: 4px solid #ffc107 !important;
        border-radius: 8px !important;
        color: var(--primary-dark) !important;
    }
    
    .stError {
        background: rgba(220, 53, 69, 0.1) !important;
        border-left: 4px solid #dc3545 !important;
        border-radius: 8px !important;
        color: var(--primary-dark) !important;
    }
    
    /* Dataframe Styling */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-gray);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: var(--primary-yellow) !important;
        border-radius: 10px;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--primary-yellow), transparent);
        margin: 1.5rem 0;
    }
    
    /* Score Badge Styling */
    .score-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 1rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .score-high {
        background: rgba(40, 167, 69, 0.15);
        color: #28a745;
        border: 1px solid rgba(40, 167, 69, 0.3);
    }
    
    .score-medium {
        background: rgba(255, 193, 7, 0.15);
        color: #d39e00;
        border: 1px solid rgba(255, 193, 7, 0.3);
    }
    
    .score-low {
        background: rgba(220, 53, 69, 0.15);
        color: #dc3545;
        border: 1px solid rgba(220, 53, 69, 0.3);
    }
    
    /* Recommendation Badges */
    .rec-pursue {
        background: #28a745;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        font-weight: 600;
        display: inline-block;
    }
    
    .rec-evaluate {
        background: var(--primary-yellow);
        color: var(--primary-dark);
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        font-weight: 600;
        display: inline-block;
    }
    
    .rec-pass {
        background: var(--text-secondary);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Popover Styling */
    [data-testid="stPopover"] {
        background: var(--primary-white) !important;
        border: 1px solid var(--border-gray) !important;
        border-radius: 12px !important;
        box-shadow: var(--card-shadow);
    }
    
    /* Radio Buttons Styling */
    [data-testid="stRadio"] > div {
        gap: 0.5rem;
    }
    
    [data-testid="stRadio"] label {
        background: var(--primary-white) !important;
        border: 1px solid var(--border-gray) !important;
        border-radius: 8px;
        padding: 0.8rem 1rem !important;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    /* Make sure text is visible in radio labels */
    [data-testid="stRadio"] label span,
    [data-testid="stRadio"] label p,
    [data-testid="stRadio"] label div {
        color: #333333 !important;
    }
    
    [data-testid="stRadio"] label:hover {
        background: rgba(255, 230, 0, 0.2) !important;
        border-color: var(--primary-yellow) !important;
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
                bid_num = bid.get('Bid Number') or bid.get('bid_number')
                
                # Progress display
                progress_container = st.empty()
                doc_path = None
                
                # FIRST check for manual upload in session state
                upload_key = f"manual_pdf_{bid_num}"
                if upload_key in st.session_state and st.session_state[upload_key] is not None:
                    # Use the manually uploaded file
                    import tempfile
                    uploaded_file = st.session_state[upload_key]
                    temp_path = os.path.join(tempfile.gettempdir(), f"{bid_num}_manual.pdf")
                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    doc_path = temp_path
                    progress_container.success("✅ Using manually uploaded PDF")
                else:
                    # Try automatic download
                    progress_container.info("📥 Step 1/3: Downloading document...")
                    doc_path = download_document(doc_link, bid_data=bid)
                
                if not doc_path:
                    progress_container.warning("⚠️ GeM requires login to download documents automatically.")
                    
                    # Show instructions with document button
                    st.markdown(f"""
                    **📄 To analyze this bid:**
                    1. [**Click here to open document in browser**]({doc_link}) (opens in new tab)
                    2. Download/save the PDF from the portal
                    3. Upload it below ⬇️
                    """)
                    
                    # File uploader for manual upload
                    uploaded_pdf = st.file_uploader(
                        "📤 Upload the bid document PDF",
                        type=['pdf'],
                        key=f"uploader_{bid_num}",
                        help="Download the document from GeM portal and upload here"
                    )
                    
                    if uploaded_pdf is not None:
                        # Save to session state and continue analysis
                        st.session_state[upload_key] = uploaded_pdf
                        st.success("✅ PDF uploaded! Processing now...")
                        # Rerun to process the uploaded file
                        st.rerun()
                    
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
                    
                    # Add sow_summary and bid_number to analysis for database and email
                    full_analysis['sow_summary'] = sow_summary
                    full_analysis['bid_number'] = bid_num
                    
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
        
        with st.expander(f"📊 Full Intelligence Report: {result['bid_num']}", expanded=True):
            # Create 2 tabs: SOW Summary and Combined Intelligence
            tab1, tab2 = st.tabs(["📋 SOW Summary", "🎯 Combined Intelligence Report"])
            
            with tab1:
                st.markdown("### Scope of Work Summary")
                st.markdown(result['sow'])
            
            with tab2:
                st.markdown("### 🎯 Combined Intelligence Report")
                
                # Extract all data
                cfs = result['cfs'].get('cfs', {})
                score = cfs.get('score', 0)
                verdict = cfs.get('verdict', 'N/A')
                rec = result['cfs'].get('go_no_go', {}).get('overall_recommendation', 'N/A')
                
                ad = result.get('ad', {}) or {}
                ad_score = ad.get('a_d_relevance_score', 0)
                ad_rec = ad.get('recommendation', 'N/A')
                ad_confidence = ad.get('confidence', 0)
                ad_category = ad.get('a_d_sub_category', 'N/A')
                
                # Combined Score Cards - 5 metrics in one row
                st.markdown("#### 📊 Key Metrics")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    score_color = "#11998e" if score >= 70 else "#f5a623" if score >= 50 else "#e74c3c"
                    st.markdown(f"""
                    <div style='text-align: center; padding: 15px; 
                         background: linear-gradient(135deg, {score_color}dd, {score_color}aa); 
                         color: white; border-radius: 12px;'>
                        <div style='font-size: 2rem; font-weight: bold;'>{score}</div>
                        <div style='font-size: 0.8rem; opacity: 0.9;'>CFS Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    rec_color = "#11998e" if rec == "GO" else "#e74c3c" if rec == "NO_GO" else "#f5a623"
                    st.markdown(f"""
                    <div style='text-align: center; padding: 15px; 
                         background: linear-gradient(135deg, {rec_color}dd, {rec_color}aa); 
                         color: white; border-radius: 12px;'>
                        <div style='font-size: 1.5rem; font-weight: bold;'>{rec}</div>
                        <div style='font-size: 0.8rem; opacity: 0.9;'>CFS Rec</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    ad_score_color = "#11998e" if ad_score >= 70 else "#f5a623" if ad_score >= 50 else "#e74c3c"
                    st.markdown(f"""
                    <div style='text-align: center; padding: 15px; 
                         background: linear-gradient(135deg, {ad_score_color}dd, {ad_score_color}aa); 
                         color: white; border-radius: 12px;'>
                        <div style='font-size: 2rem; font-weight: bold;'>{ad_score:.0f}</div>
                        <div style='font-size: 0.8rem; opacity: 0.9;'>A&D Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    ad_rec_color = "#11998e" if ad_rec == "PURSUE" else "#e74c3c" if ad_rec == "PASS" else "#f5a623"
                    st.markdown(f"""
                    <div style='text-align: center; padding: 15px; 
                         background: linear-gradient(135deg, {ad_rec_color}dd, {ad_rec_color}aa); 
                         color: white; border-radius: 12px;'>
                        <div style='font-size: 1.5rem; font-weight: bold;'>{ad_rec}</div>
                        <div style='font-size: 0.8rem; opacity: 0.9;'>A&D Action</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 15px; 
                         background: linear-gradient(135deg, #667eeadd, #764ba2aa); 
                         color: white; border-radius: 12px;'>
                        <div style='font-size: 1.1rem; font-weight: bold;'>{verdict}</div>
                        <div style='font-size: 0.8rem; opacity: 0.9;'>Verdict</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Combined Details in 2 columns
                col_left, col_right = st.columns(2)
                
                with col_left:
                    st.markdown("#### 💡 CFS Analysis")
                    
                    # Reasoning
                    if cfs.get('reasoning'):
                        st.info(cfs['reasoning'])
                    
                    # Executive Summary
                    exec_summary = result['cfs'].get('executive_summary', {})
                    if exec_summary and isinstance(exec_summary, dict):
                        if exec_summary.get('the_ask'):
                            st.markdown(f"**🎯 The Ask:** {exec_summary['the_ask']}")
                        if exec_summary.get('key_deliverables'):
                            st.markdown("**📦 Key Deliverables:**")
                            for d in exec_summary['key_deliverables'][:5]:
                                st.markdown(f"  • {d}")
                
                with col_right:
                    st.markdown("#### 📊 A&D Intelligence")
                    
                    if result.get('has_ad') and ad:
                        # Category and Confidence
                        st.markdown(f"**🏷️ Category:** {ad_category}")
                        st.markdown(f"**🎯 Confidence:** {ad_confidence:.0f}%")
                        
                        # Risk Assessment
                        risk = ad.get('risk_assessment', {})
                        if risk:
                            st.markdown("**⚠️ Risk Assessment:**")
                            risk_items = [
                                ("Implementation", risk.get('implementation_risk', 'N/A')),
                                ("Scope Creep", risk.get('scope_creep_risk', 'N/A')),
                                ("Political", risk.get('political_risk', 'N/A')),
                                ("Win Prob.", risk.get('win_probability', 'N/A'))
                            ]
                            for label, value in risk_items:
                                color = "#11998e" if value == "Low" else "#f5a623" if value == "Medium" else "#e74c3c"
                                st.markdown(f"  • **{label}:** <span style='color: {color}'>{value}</span>", unsafe_allow_html=True)
                        
                        # Matched Keywords
                        keywords = ad.get('matched_keywords', [])
                        if keywords:
                            st.markdown(f"**🏷️ Keywords:** {', '.join(str(k) for k in keywords[:10])}")
                    else:
                        st.info("A&D Intelligence not available for this bid.")
            
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

# Initialize authentication
init_session()

# Initialize database
if 'db' not in st.session_state:
    st.session_state.db = CIPDatabase()
    
if 'auth_manager' not in st.session_state:
    st.session_state.auth_manager = AuthManager()

# Initialize agent
if 'agent' not in st.session_state:
    st.session_state.agent = CIPAgent()

# ============== LOGIN/REGISTER PAGE ==============
if not is_logged_in():
    # Capture any deep link params BEFORE login (will use after successful login)
    query_params = st.query_params
    if 'bidId' in query_params:
        st.session_state['pending_bid_id'] = query_params.get('bidId')
    
    # Center the login card
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: #1a1a2e; margin-bottom: 5px;'>🎯 CIP</h1>
            <p style='color: #666; font-size: 14px;'>Consulting Intelligence Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if Google OAuth is properly configured (not placeholder values)
        google_configured = False
        if os.path.exists("google_credentials.json"):
            try:
                import json
                with open("google_credentials.json", "r") as f:
                    creds = json.load(f)
                    client_id = creds.get("web", {}).get("client_id", "")
                    # Only use OAuth if real credentials are set (not placeholders)
                    if client_id and "YOUR_GOOGLE_CLIENT_ID" not in client_id:
                        google_configured = True
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                google_configured = False
        
        if google_configured:
            try:
                # Try to use real Google OAuth
                from streamlit_google_auth import Authenticate
                
                authenticator = Authenticate(
                    secret_credentials_path='google_credentials.json',
                    cookie_name='cip_auth',
                    cookie_key=os.environ.get('CIP_SECRET_KEY', 'cip_secret_key_dev_only'),
                    redirect_uri='http://localhost:8518',
                )
                
                # Check if already authenticated via Google
                authenticator.check_authentification()
                
                if st.session_state.get('connected'):
                    # User is authenticated via Google
                    google_info = {
                        "email": st.session_state.get('user_info', {}).get('email', ''),
                        "name": st.session_state.get('user_info', {}).get('name', ''),
                        "sub": st.session_state.get('user_info', {}).get('id', ''),
                        "picture": st.session_state.get('user_info', {}).get('picture', '')
                    }
                    
                    result = st.session_state.auth_manager.login_with_google(google_info)
                    if result["success"]:
                        login_user(result["user"])
                        st.rerun()
                else:
                    # Show Google Sign-In button
                    st.markdown("### Sign in to continue")
                    
                    # Google login button from library
                    authenticator.login()
                    
            except Exception as e:
                st.warning(f"Google OAuth error: {str(e)[:100]}")
                google_configured = False
        
        if not google_configured:
            st.markdown("### Sign in to continue")
            
            # Manual Google-style login for demo/testing
            with st.container(border=True):
                st.markdown("#### 🔵 Continue with Google")
                st.caption("Enter your Google account details")
                
                demo_name = st.text_input("Name", placeholder="Manoj", key="google_name")
                demo_email = st.text_input("Email", placeholder="manojgundeti1234@gmail.com", key="google_email")
                
                if demo_name and demo_email:
                    # Show preview
                    initial = demo_name[0].upper()
                    st.markdown(f"""
                    <div style='display: flex; align-items: center; gap: 12px; padding: 12px 16px; 
                         background: #f8f9fa; border: 1px solid #dadce0; border-radius: 8px; margin: 10px 0;'>
                        <div style='width: 40px; height: 40px; border-radius: 50%; 
                             background: linear-gradient(135deg, #667eea, #764ba2);
                             display: flex; align-items: center; justify-content: center;
                             color: white; font-weight: bold; font-size: 16px;'>{initial}</div>
                        <div style='flex: 1;'>
                            <div style='font-size: 14px; font-weight: 500; color: #202124;'>Continue as {demo_name}</div>
                            <div style='font-size: 12px; color: #5f6368;'>{demo_email} ▾</div>
                        </div>
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="24">
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🔵 Continue with Google", type="primary", use_container_width=True):
                        google_info = {
                            "email": demo_email,
                            "name": demo_name,
                            "sub": f"google_{demo_email.replace('@', '_').replace('.', '_')}",
                            "picture": ""
                        }
                        result = st.session_state.auth_manager.login_with_google(google_info)
                        if result["success"]:
                            login_user(result["user"])
                            st.success(f"Welcome, {result['user']['username']}!")
                            st.rerun()
                        else:
                            st.error(result["error"])
        
        # OR Divider
        st.markdown("""
        <div style='display: flex; align-items: center; margin: 25px 0; color: #5f6368;'>
            <div style='flex: 1; height: 1px; background: #dadce0;'></div>
            <span style='padding: 0 16px; font-size: 14px;'>OR</span>
            <div style='flex: 1; height: 1px; background: #dadce0;'></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Email Login Toggle
        if 'show_email_login' not in st.session_state:
            st.session_state.show_email_login = False
        
        if st.button("📧 Login with Email", use_container_width=True):
            st.session_state.show_email_login = not st.session_state.show_email_login
        
        if st.session_state.show_email_login:
            with st.container(border=True):
                login_username = st.text_input("Username or Email", key="login_user")
                login_password = st.text_input("Password", type="password", key="login_pass")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("🔓 Login", type="primary", use_container_width=True):
                        if login_username and login_password:
                            result = st.session_state.auth_manager.login(login_username, login_password)
                            if result["success"]:
                                login_user(result["user"])
                                st.rerun()
                            else:
                                st.error(result["error"])
                
                with col_b:
                    if st.button("📝 Register", use_container_width=True):
                        st.session_state.show_register = not st.session_state.get('show_register', False)
                
                if st.session_state.get('show_register'):
                    st.divider()
                    reg_username = st.text_input("Username", key="reg_user")
                    reg_email = st.text_input("Email", key="reg_email")
                    reg_password = st.text_input("Password", type="password", key="reg_pass")
                    reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
                    
                    if st.button("Create Account", type="primary", use_container_width=True):
                        if reg_password != reg_confirm:
                            st.error("Passwords don't match")
                        else:
                            result = st.session_state.auth_manager.register_user(reg_username, reg_email, reg_password)
                            if result["success"]:
                                st.success("Account created! Please login.")
                            else:
                                st.error(result["error"])
        
        # Setup instructions
        with st.expander("🔧 Setup Real Google OAuth"):
            st.markdown("""
            To enable one-click Google Sign-In:
            
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project or select existing
            3. Enable **Google+ API** and **OAuth consent screen**
            4. Create **OAuth 2.0 credentials** (Web application)
            5. Add `http://localhost:8516` to authorized redirect URIs
            6. Download the credentials JSON
            7. Replace `google_credentials.json` content with your credentials
            
            Once configured, users can sign in with one click!
            """)
    
    st.stop()

# ============== MAIN APP (LOGGED IN) ==============

# Initialize results if empty
if 'current_results' not in st.session_state:
    st.session_state['current_results'] = st.session_state.db.get_recent_bids_with_analysis(limit=20)

# Sidebar
with st.sidebar:
    st.title("🎯 CIP")
    st.markdown("**Consulting Intelligence Platform**")
    
    # User info
    user = get_current_user()
    if user:
        st.caption(f"👤 {user['username']} {'(Admin)' if user['is_admin'] else ''}")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    st.divider()
    
    # Navigation - Admin page visible only to admins
    base_pages = ["🔎 Scraper", "⭐ Watchlist", "📊 Analytics"]
    if is_admin():
        base_pages.append("🔧 Admin")
    
    page = st.radio(
        "Navigation",
        base_pages,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Firm Profile Summary
    with st.expander("📋 Firm Profile"):
        st.markdown(f"**{FIRM_PROFILE['name']}**")
        st.caption(f"Focus Areas: {len(FIRM_PROFILE['expertise_areas'])} domains")
        st.caption(f"Min CFS Score: {NOTIFICATION_CONFIG['min_cfs_score']}")

# Page 1: Scraper (Main feature with sub-tabs)
if page == "🔎 Scraper":
    st.title("🔎 Scraper")
    st.caption("AI-powered bid discovery, scraping & search")
    
    # Check for deep link from email (bidId query parameter OR pending from login)
    query_params = st.query_params
    bid_id_to_load = None
    
    # Priority 1: Check query params
    if 'bidId' in query_params:
        bid_id_to_load = query_params.get('bidId')
        st.query_params.clear()  # Clear to avoid reload loop
    
    # Priority 2: Check pending bid from before login
    elif 'pending_bid_id' in st.session_state:
        bid_id_to_load = st.session_state.pop('pending_bid_id')
    
    # Load the bid if we have an ID
    if bid_id_to_load:
        st.info(f"📧 Opening bid from email: **{bid_id_to_load}**")
        
        # Load this specific bid from database
        try:
            all_results = st.session_state.db.get_recent_bids_with_analysis(limit=200)
            # Filter to find the matching bid
            matching_bids = [r for r in all_results if r.get('Bid Number') == bid_id_to_load or r.get('bid_id') == bid_id_to_load]
            
            if matching_bids:
                st.session_state['current_results'] = matching_bids
                st.session_state['deep_link_bid'] = bid_id_to_load
                st.success(f"✅ Found bid {bid_id_to_load}")
            else:
                st.warning(f"⚠️ Bid {bid_id_to_load} not found in history. Loading all recent bids...")
                st.session_state['current_results'] = all_results[:50]
        except Exception as e:
            st.error(f"Error loading bid: {str(e)}")
    
    # Sub-tabs for different scraper features
    scraper_tab1, scraper_tab2, scraper_tab3 = st.tabs(["📅 Daily Scraper", "🔍 Intelligence Search", "📂 Search History"])
    
    # ============ TAB 1: Daily Scraper ============
    with scraper_tab1:
        st.markdown("### Daily Scraper (Last 24 Hours)")
        st.caption("Scrape and analyze bids published in the last 24 hours")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            daily_scrape = st.button("▶️ Run Daily Scrape Now", type="primary", use_container_width=True)
        with col3:
            load_from_db = st.button("📂 Load Saved Bids", use_container_width=True, help="Load previously scraped bids from database")

        with col2:
            show_email_options = st.button("📧 Email Report", key="daily_email_btn", use_container_width=True)
        
        # Email Options Panel (appears when button is clicked)
        if show_email_options or st.session_state.get('show_email_panel', False):
            st.session_state['show_email_panel'] = True
            
            if 'current_results' not in st.session_state or not st.session_state['current_results']:
                st.warning("⚠️ Run a scrape first to generate a report.")
                st.session_state['show_email_panel'] = False
            else:
                with st.expander("📧 Email Options", expanded=True):
                    results = st.session_state['current_results']
                    
                    # Get team emails from database
                    team_emails = get_team_emails()
                    
                    # Recipient Selection
                    st.markdown("**Select Recipients:**")
                    recipient_option = st.radio(
                        "Send to:",
                        ["All Team Members", "Select Specific Recipients"],
                        key="email_recipient_option",
                        horizontal=True
                    )
                    
                    if recipient_option == "Select Specific Recipients":
                        selected_recipients = st.multiselect(
                            "Choose recipients:",
                            options=team_emails,
                            default=[],
                            key="email_selected_recipients"
                        )
                        # Option to add custom email
                        custom_email = st.text_input("Or add a custom email:", placeholder="example@email.com", key="email_custom")
                        if custom_email and custom_email not in selected_recipients:
                            selected_recipients.append(custom_email)
                    else:
                        selected_recipients = team_emails
                    
                    st.divider()
                    
                    # Bid Selection
                    st.markdown("**Select Bids to Include:**")
                    bid_option = st.radio(
                        "Include:",
                        ["All Bids", "Select Specific Bids"],
                        key="email_bid_option",
                        horizontal=True
                    )
                    
                    if bid_option == "Select Specific Bids":
                        # Create bid options with labels
                        bid_options = {f"{b.get('Bid Number', 'N/A')[:20]} - {b.get('Items', 'N/A')[:40]}": i for i, b in enumerate(results)}
                        selected_bid_labels = st.multiselect(
                            "Choose bids:",
                            options=list(bid_options.keys()),
                            default=[],
                            key="email_selected_bids"
                        )
                        selected_bids = [results[bid_options[label]] for label in selected_bid_labels]
                    else:
                        selected_bids = results
                    
                    st.divider()
                    
                    # Summary and Send
                    col_summary1, col_summary2 = st.columns(2)
                    with col_summary1:
                        st.metric("Recipients", len(selected_recipients))
                    with col_summary2:
                        st.metric("Bids", len(selected_bids))
                    
                    col_send, col_cancel = st.columns(2)
                    with col_send:
                        if st.button("📨 Send Email", type="primary", use_container_width=True, key="send_email_confirm"):
                            if not selected_recipients:
                                st.error("Please select at least one recipient.")
                            elif not selected_bids:
                                st.error("Please select at least one bid.")
                            else:
                                from email_notifier import send_email_digest
                                # Adapt bids for email
                                adapted_bids = []
                                for bid in selected_bids:
                                    cfs = {
                                        'score': bid.get('CFS Score') or 0,
                                        'verdict': bid.get('Verdict', 'N/A'),
                                        'reasoning': bid.get('Reasoning', 'N/A')
                                    }
                                    go_no_go = {'overall_recommendation': bid.get('Recommendation', 'N/A')}
                                    adapted_bids.append({
                                        'bid': bid,
                                        'analysis': {'cfs': cfs, 'go_no_go': go_no_go},
                                        'sow_summary': bid.get('sow_summary', '')
                                    })
                                
                                subject = f"📊 Daily Scraper: {len(selected_bids)} Bids - {datetime.now().strftime('%d %b %Y')}"
                                success = send_email_digest(adapted_bids, recipient_emails=selected_recipients, subject=subject)
                                
                                if success:
                                    st.success(f"✅ Email sent to {len(selected_recipients)} recipients!")
                                    st.session_state['show_email_panel'] = False
                                else:
                                    st.error("❌ Failed to send email. Check logs.")
                    
                    with col_cancel:
                        if st.button("Cancel", use_container_width=True, key="cancel_email"):
                            st.session_state['show_email_panel'] = False
                            st.rerun()
        
        # Handle Load from Database button
        if load_from_db:
            with st.spinner("📂 Loading bids from database..."):
                try:
                    from database import CIPDatabase
                    db = CIPDatabase()
                    saved_bids = db.get_recent_bids_with_analysis(limit=500)
                    if saved_bids:
                        # Convert database format to display format
                        loaded_results = []
                        for bid in saved_bids:
                            loaded_bid = {
                                'Bid Number': bid.get('bid_number', ''),
                                'Items': bid.get('title', bid.get('items', '')),
                                'Department': bid.get('department', ''),
                                'Start Date': bid.get('start_date', ''),
                                'End Date': bid.get('end_date', ''),
                                'Document Link': bid.get('document_link', bid.get('budget', '')),
                                'Source Portal': bid.get('source_portal', 'gem'),
                                'Intent Analysis': bid.get('ai_summary', 'N/A'),
                                'Primary Archetype': bid.get('primary_archetype', 'N/A'),
                                'Priority Band': bid.get('priority_band', 'MEDIUM'),
                                'Action': bid.get('action', 'Review'),
                                'Confidence': bid.get('confidence_score', 0),
                            }
                            loaded_results.append(loaded_bid)
                        st.session_state['current_results'] = loaded_results
                        st.success(f"✅ Loaded {len(loaded_results)} bids from database")
                    else:
                        st.info("No saved bids found in database. Run a scrape first.")
                except Exception as e:
                    st.error(f"Error loading from database: {e}")
        
        if daily_scrape:

            with st.spinner("🔄 Scraping bids from last 24 hours..."):
                try:
                    # Calculate 24 hours ago
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    # Use Unified Scraper for Daily Scrape (Default to GeM + Others if configured)
                    unified = UnifiedScraper()
                    
                    # Combine all search terms - use FULL organization names for comprehensive coverage
                    # ALL_DEFENCE_ORGANIZATIONS includes MOD_ORGANIZATIONS + DEFENCE_PSUS (~200 orgs)
                    all_keywords = list(KEYWORD_EXPANSIONS.keys()) + ALL_DEFENCE_ORGANIZATIONS + DEFENCE_ORG_KEYWORDS
                    # Determine unique keywords to avoid redundant searches if overlaps exist
                    unique_keywords = list(set(all_keywords))
                    
                    st.info(f"🔎 Scraping with {len(unique_keywords)} keywords (including all Defence orgs)...")
                    
                    bids = unified.scrape(
                        portals=['gem', 'cppp', 'dppp', 'goa_shipyard', 'ddp'],
                        keywords=unique_keywords,
                        from_date=yesterday,
                        to_date=today,
                        max_pages=5,
                        consulting_only=True,
                        date_filter_type='start'
                    )
                    
                    if bids:
                        # Show breakdown by portal
                        portal_counts = {}
                        for bid in bids:
                            portal = bid.get('Source Portal', 'unknown')
                            portal_counts[portal] = portal_counts.get(portal, 0) + 1
                        
                        breakdown = ", ".join([f"{p.upper()}: {c}" for p, c in portal_counts.items()])
                        st.success(f"✅ Found {len(bids)} bids ({breakdown})")
                        
                        # Apply Intent-Driven v4.1 analysis
                        with st.spinner("🤖 Applying Intent-Driven v4.1 analysis..."):
                            try:
                                from intent_scorer import analyze_bid_intent, IntentDrivenScorer
                                
                                # Apply pre-filter to exclude non-consulting bids early
                                # Note: DPSU portals (goa_shipyard, ddp) bypass prefilter as they're already defence-focused
                                DPSU_PORTALS = ['goa_shipyard', 'ddp', 'grse', 'bdl', 'hal', 'bhel']
                                scorer = IntentDrivenScorer()
                                pre_filtered_bids = []
                                skipped_count = 0
                                for bid in bids:
                                    source_portal = bid.get('Source Portal', '').lower()
                                    # DPSU portals bypass prefilter - include all their bids
                                    if source_portal in DPSU_PORTALS:
                                        pre_filtered_bids.append(bid)
                                    elif scorer.quick_prefilter(bid):
                                        pre_filtered_bids.append(bid)
                                    else:
                                        skipped_count += 1
                                
                                if skipped_count > 0:
                                    st.info(f"🔍 Pre-filter: Skipped {skipped_count} non-consulting bids (supplies, equipment, medicine, etc.)")
                                
                                if not pre_filtered_bids:
                                    st.warning("⚠️ No consulting-related bids found after filtering.")
                                    st.session_state['current_results'] = []
                                else:
                                    analyzed_results = []
                                    progress_bar = st.progress(0)
                                    for idx, bid in enumerate(pre_filtered_bids):
                                        intent_analysis = analyze_bid_intent(bid)
                                        # Merge intent analysis results into bid
                                        enriched_bid = {
                                            **bid,
                                            'Intent Analysis': intent_analysis.get('buyer_intent', 'N/A'),
                                            'Primary Archetype': intent_analysis.get('primary_archetype', 'N/A'),
                                            'Priority Band': intent_analysis.get('priority_band', 'LOW'),
                                            'Action': intent_analysis.get('action', 'Review'),
                                            'Dominant Risk': intent_analysis.get('dominant_risk', 'N/A'),
                                            'Confidence': intent_analysis.get('confidence_scores', {}).get('final_percent', 0),
                                            'intent_analysis_full': intent_analysis
                                        }
                                        analyzed_results.append(enriched_bid)
                                        progress_bar.progress((idx + 1) / len(pre_filtered_bids))
                                    st.session_state['current_results'] = analyzed_results
                                    
                                    # Save bids to database for persistence
                                    try:
                                        from database import CIPDatabase
                                        db = CIPDatabase()
                                        saved_count = 0
                                        for bid in analyzed_results:
                                            db.save_bid(bid)
                                            saved_count += 1
                                        st.info(f"💾 Saved {saved_count} bids to database")
                                    except Exception as save_error:
                                        st.warning(f"⚠️ Could not save to database: {save_error}")
                                    
                                    # ========== AUTO FULL ANALYSIS ==========
                                    # Run Full Analysis (SOW + CFS) on HIGH priority bids automatically
                                    high_priority_bids = [b for b in analyzed_results if b.get('Priority Band') == 'HIGH']
                                    
                                    if high_priority_bids:
                                        st.info(f"🤖 Running Full Analysis on {len(high_priority_bids)} HIGH priority bids...")
                                        analysis_progress = st.progress(0)
                                        analysis_status = st.empty()
                                        
                                        for idx, bid in enumerate(high_priority_bids):
                                            bid_num = bid.get('Bid Number', 'Unknown')
                                            doc_link = bid.get('Document Link', '')
                                            
                                            analysis_status.text(f"Analyzing {idx+1}/{len(high_priority_bids)}: {bid_num[:30]}...")
                                            
                                            try:
                                                # Check if already analyzed
                                                cached_analysis = db.get_bid_with_analysis(bid_num)
                                                if cached_analysis and cached_analysis.get('sow_summary'):
                                                    # Already analyzed, skip
                                                    analysis_progress.progress((idx + 1) / len(high_priority_bids))
                                                    continue
                                                
                                                # Download document
                                                doc_path = None
                                                if doc_link:
                                                    from gem_scraper import download_document
                                                    doc_path = download_document(doc_link, bid_data=bid)
                                                
                                                # If download failed (GeM requires login), skip this bid
                                                if not doc_path:
                                                    analysis_progress.progress((idx + 1) / len(high_priority_bids))
                                                    continue
                                                
                                                # Extract SOW using VirtualAgent
                                                from virtual_agent import BidReaderAgent
                                                agent = BidReaderAgent(doc_path)
                                                sow_summary = agent.summarize_sow()
                                                
                                                # Run CFS Analysis
                                                from ai_analyzer import analyze_bid_complete
                                                full_analysis = analyze_bid_complete(bid, sow_text=sow_summary, pdf_path=doc_path)
                                                
                                                # Add sow_summary and bid_number to analysis
                                                full_analysis['sow_summary'] = sow_summary
                                                full_analysis['bid_number'] = bid_num
                                                
                                                # Save to database
                                                db.save_ai_analysis(full_analysis)
                                                
                                                # Update the bid in analyzed_results with CFS score
                                                bid['CFS Score'] = full_analysis.get('cfs', {}).get('score', 0)
                                                bid['Verdict'] = full_analysis.get('cfs', {}).get('verdict', 'N/A')
                                                bid['Recommendation'] = full_analysis.get('go_no_go', {}).get('overall_recommendation', 'N/A')
                                                bid['sow_summary'] = sow_summary
                                                
                                            except Exception as analysis_error:
                                                st.warning(f"⚠️ Could not analyze {bid_num[:20]}: {str(analysis_error)[:50]}")
                                            
                                            analysis_progress.progress((idx + 1) / len(high_priority_bids))
                                        
                                        analysis_status.empty()
                                        st.success(f"✅ Full Analysis complete for HIGH priority bids!")
                                        st.session_state['current_results'] = analyzed_results  # Update with CFS scores
                                    
                                    # ========== END AUTO FULL ANALYSIS ==========
                                    
                                    # Show summary
                                    high_priority = len([b for b in analyzed_results if b.get('Priority Band') == 'HIGH'])
                                    medium_priority = len([b for b in analyzed_results if b.get('Priority Band') == 'MEDIUM'])
                                    st.success(f"✅ Analyzed {len(analyzed_results)} bids: {high_priority} HIGH, {medium_priority} MEDIUM priority")
                            except ImportError as e:
                                st.warning(f"Intent scorer not available: {e}. Using basic results.")
                                st.session_state['current_results'] = bids
                            except Exception as e:
                                st.error(f"Analysis error: {e}")
                                st.session_state['current_results'] = bids

                    else:
                        st.info("No new bids found in the last 24 hours")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # ============ TAB 2: Intelligence Search ============
    with scraper_tab2:
        st.markdown("### Intelligence Search")
        st.caption("Search government procurement portals with custom filters and AI analysis")
        
        # Portal Selection
        st.markdown("**Select Portals to Search:**")
        portal_cols = st.columns(3)
        with portal_cols[0]:
            search_gem = st.checkbox("🛒 GeM", value=True, key="portal_gem")
        with portal_cols[1]:
            search_cppp = st.checkbox("📜 CPPP", value=True, key="portal_cppp", help="Central Public Procurement Portal")
        with portal_cols[2]:
            search_dppp = st.checkbox("🛡️ DPPP", value=True, key="portal_dppp", help="Defence Procurement Portal")
        
        st.divider()
        
        # Row 1: Keywords
        keywords = st.text_input(
            "🔑 Keywords",
            placeholder="e.g., Digital Transformation, ERP, Cloud, Consultancy",
            help="Enter keywords to search for specific opportunities",
            key="intel_keywords"
        )
        
        # Row 2: Organization/Ministry Filter + Date Range
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Combined organization list for dropdown
            organization_options = ["All Organizations"] + sorted(ALL_DEFENCE_ORGANIZATIONS)
            selected_org = st.selectbox(
                "🏛️ Organization / Ministry",
                options=organization_options,
                index=0,
                help="Select an organization or ministry to filter",
                key="intel_org"
            )
            organization_filter = "" if selected_org == "All Organizations" else selected_org
        
        with col2:
            from_date = st.date_input(
                "📅 From Date",
                value=datetime.now() - timedelta(days=30),
                key="intel_from"
            )
        
        with col3:
            to_date = st.date_input(
                "📅 To Date",
                value=datetime.now(),
                key="intel_to"
            )
        
        # Row 3: Advanced Options
        with st.expander("⚙️ Advanced Options"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                max_pages = st.slider("Max Pages", 1, 20, 5, key="intel_pages")
            with col2:
                consulting_only = st.checkbox("Consulting Only", value=True, key="intel_consult")
            with col3:
                run_ai_analysis = st.checkbox("Run Full Analysis", value=True, help="SOW + CFS + A&D", key="intel_ai")
            with col4:
                use_cached = st.checkbox("Use Cached", value=True, key="intel_cache")
        
        # Search button
        if st.button("🚀 Run Search", type="primary", use_container_width=True, key="intel_search_btn"):
            # Determine which portals to search
            from portal_scrapers import UnifiedScraper, PortalType
            
            selected_portals = []
            if search_gem:
                selected_portals.append(PortalType.GEM)
            if search_cppp:
                selected_portals.append(PortalType.CPPP)
            if search_dppp:
                selected_portals.append(PortalType.DPPP)
            
            if not selected_portals:
                st.warning("⚠️ Please select at least one portal to search")
            else:
                portal_names = ", ".join([p.name for p in selected_portals])
                with st.spinner(f"Searching {portal_names}..."):
                    try:
                        unified_scraper = UnifiedScraper()
                        # Convert PortalType enums to string values
                        portal_values = [p.value for p in selected_portals]
                        
                        bids = unified_scraper.scrape(
                            portals=portal_values,
                            keywords=keywords,
                            from_date=from_date.strftime('%Y-%m-%d') if from_date else "",
                            to_date=to_date.strftime('%Y-%m-%d') if to_date else "",
                            max_pages=max_pages,
                            consulting_only=consulting_only
                        )
                        
                        # Results are already dicts from UnifiedScraper.scrape
                        # bids variable is already populated
                        
                        # Normalize keys if needed (UnifiedScraper returns consistent dicts)
                        
                        # Apply organization filter if provided
                        if organization_filter and bids:
                            org_lower = organization_filter.lower()
                            bids = [b for b in bids if org_lower in b.get('Department', '').lower()]
                    except Exception as e:
                        st.error(f"Error searching portals: {str(e)}")
                        bids = []
                
                from gem_scraper import filter_new_bids
                
                if bids:
                    st.info(f"📊 Found {len(bids)} matching bids")
                    new_bids, existing_bids = filter_new_bids(bids, st.session_state.db)
                    st.success(f"✨ {len(new_bids)} NEW | 📁 {len(existing_bids)} cached")
                    
                    analyzed_bids = []
                    
                    # Load cached
                    if use_cached and existing_bids:
                        for bid in existing_bids:
                            cached = st.session_state.db.get_bid_with_analysis(bid['Bid Number'])
                            if cached:
                                analyzed_bids.append({**bid, 'CFS Score': cached.get('cfs_score', 0), 
                                    'Verdict': cached.get('cfs_verdict', 'N/A'),
                                    'Recommendation': cached.get('go_no_go_recommendation', 'N/A'), '_cached': True})
                            else:
                                new_bids.append(bid)
                    
                    # Analyze new
                    if new_bids and run_ai_analysis:
                        progress = st.progress(0)
                        for i, bid in enumerate(new_bids):
                            st.session_state.db.save_bid(bid)
                            try:
                                doc_path = download_document(bid.get('Document Link', ''), bid_data=bid)
                                sow = ""
                                if doc_path:
                                    try:
                                        sow = BidReaderAgent(doc_path).summarize_sow()
                                    except Exception:  # SOW extraction may fail for various reasons
                                        pass
                                analysis = analyze_bid_complete(bid, pdf_path=doc_path, sow_text=sow)
                                st.session_state.db.save_ai_analysis(analysis)
                                analyzed_bids.append({**bid, 'CFS Score': analysis['cfs']['score'],
                                    'Verdict': analysis['cfs']['verdict'],
                                    'Recommendation': analysis['go_no_go']['overall_recommendation'], '_new': True})
                            except Exception as e:
                                analyzed_bids.append({**bid, 'CFS Score': 0, 'Verdict': 'Error', 'Recommendation': 'N/A'})
                            progress.progress((i + 1) / len(new_bids))
                        progress.empty()
                    elif new_bids:
                        for bid in new_bids:
                            st.session_state.db.save_bid(bid)
                            analyzed_bids.append(bid)
                    
                    analyzed_bids.sort(key=lambda x: x.get('CFS Score') or 0, reverse=True)
                    st.session_state['current_results'] = analyzed_bids
                    st.success(f"✅ Complete! {len(analyzed_bids)} bids loaded")
                else:
                    st.warning("No bids found matching your criteria")
    
    # ============ TAB 3: Search History (DB Search) ============
    with scraper_tab3:
        st.markdown("### Search History")
        st.caption("Search your database by Bid ID or keywords")
        
        # Search input
        search_query = st.text_input(
            "🔍 Search",
            placeholder="Enter Bid ID (e.g., GEM/2024/B/...) or keywords",
            help="Search in saved bids database by ID, title, ministry, or keywords",
            key="history_search"
        )
        
        # Date range filter
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            history_from = st.date_input("From", value=datetime.now() - timedelta(days=90), key="hist_from")
        with col2:
            history_to = st.date_input("To", value=datetime.now(), key="hist_to")
        with col3:
            limit = st.selectbox("Limit", [50, 100, 200, 500], index=3, key="hist_limit")
        
        # Search button
        col1, col2 = st.columns(2)
        with col1:
            search_db = st.button("🔍 Search Database", type="primary", use_container_width=True, key="search_db_btn")
        with col2:
            load_all = st.button("📂 Load All History", use_container_width=True, key="load_all_btn")
        
        if search_db or load_all:
            with st.spinner("Searching database..."):
                try:
                    all_results = st.session_state.db.get_recent_bids_with_analysis(limit=limit)
                    
                    if search_query and not load_all:
                        query_lower = search_query.lower()
                        # Search by bid ID, title, ministry, department
                        filtered = [r for r in all_results if 
                            query_lower in r.get('Bid Number', '').lower() or
                            query_lower in r.get('Items', '').lower() or
                            query_lower in r.get('Department', '').lower() or
                            query_lower in r.get('Organisation', '').lower() or
                            query_lower in str(r.get('sow_summary', '')).lower()
                        ]
                        st.session_state['current_results'] = filtered
                        st.success(f"✅ Found {len(filtered)} matching bids")
                    else:
                        st.session_state['current_results'] = all_results
                        st.success(f"✅ Loaded {len(all_results)} bids from history")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
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
            filtered_results = [r for r in results if (r.get('CFS Score') or 0) >= min_score]
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
                        
                        # Category and Source Badge
                        badges = []
                        if 'Category' in bid:
                            badges.append(f"📂 {bid['Category']}")
                        
                        source = bid.get('Source Portal', 'gem').upper()
                        source_color = "#ff9900" if source == "GEM" else "#007bff" if source == "CPPP" else "#28a745"
                        badges.append(f"<span style='background-color: {source_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;'>{source}</span>")
                        
                        st.markdown(" ".join(badges), unsafe_allow_html=True)
                    
                    with col2:
                        # CFS Score badge
                        if 'CFS Score' in bid:
                            score = bid.get('CFS Score') or 0
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
                        st.link_button("📄 Document", bid.get('Document Link') or '#')
                    with col3:
                        display_links_button(bid, f"dashboard_{i}")
                    with col4:
                        display_full_analysis_button(bid, f"dashboard_{i}")
                
                # Display analysis results in full width (outside columns)
                run_and_display_analysis(bid, f"dashboard_{i}")
        
        else:  # Table view
            df = pd.DataFrame(filtered_results)
            # Reorder columns
            column_order = ['Bid Number', 'Source Portal', 'Category', 'CFS Score', 'Verdict', 
                           'Items', 'Department', 'End Date', 'Recommendation']
            display_columns = [col for col in column_order if col in df.columns]
            st.dataframe(df[display_columns], use_container_width=True, hide_index=True)
        
        # Export options
        st.divider()
        col1, col2, col3 = st.columns(3)
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
            # Prepare JSON data
            json_data = json.dumps(filtered_results, indent=2, default=str)
            
            st.download_button(
                "📥 Download JSON (with AI data)",
                data=json_data,
                file_name=f"cip_results_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        with col3:
            # Email to Team
            if st.button("📧 Email to Team", key="email_results_btn", use_container_width=True):
                trigger_team_email(filtered_results, source_name="Intelligence Data")





# Page 2: Watchlist
elif page == "⭐ Watchlist":
    st.title("⭐ Watchlist")
    st.caption("Track important bids and get change alerts")
    
    watchlist = st.session_state.db.get_watchlist()
    
    if not watchlist:
        st.info("📌 Your watchlist is empty. Add bids from the Intelligence Dashboard!")
    else:
        st.success(f"Monitoring {len(watchlist)} bids")
        
        watchlist_bids = []
        for bid_number in watchlist:
            bid_data = st.session_state.db.get_bid_with_analysis(bid_number)
            
            if bid_data:
                watchlist_bids.append(bid_data)
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
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Check for Updates", type="primary", use_container_width=True):
                with st.spinner("Checking watchlist..."):
                    st.session_state.agent.monitor_watchlist()
                    st.success("Watchlist checked!")
        with col2:
             if st.button("📧 Email Watchlist to Team", key="email_watchlist_btn", use_container_width=True):
                trigger_team_email(watchlist_bids, source_name="Watchlist")

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

# Page 4: Admin (Admin Only)
elif page == "🔧 Admin":
    st.title("🔧 Admin Dashboard")
    st.caption("Manage platform settings, users, and configurations")
    
    # Admin sub-navigation
    admin_tab = st.radio(
        "Admin Section",
        ["📋 Firm Profile", "🔑 Keywords & Taxonomy", "⚙️ Scraping Settings", "📧 Email Management", "👥 Users"],
        horizontal=True
    )
    
    st.divider()
    
    if admin_tab == "📋 Firm Profile":
        st.subheader("📋 Firm Profile Management")
        st.info("Configure your firm's expertise areas and preferences")
        
        # Display current settings
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Current Firm Name:**")
            st.code(FIRM_PROFILE['name'])
            
            st.markdown("**Turnover Threshold:**")
            st.code(f"₹{FIRM_PROFILE['turnover_threshold']:,}")
        
        with col2:
            st.markdown("**Min CFS Score for Digest:**")
            st.code(NOTIFICATION_CONFIG['min_cfs_score'])
            
            st.markdown("**Email Notifications:**")
            st.code("Enabled" if NOTIFICATION_CONFIG.get('enable_email') else "Disabled")
        
        st.markdown("**Expertise Areas:**")
        expertise_text = "\n".join([f"• {area}" for area in FIRM_PROFILE['expertise_areas']])
        st.text_area("Current Expertise Areas", value=expertise_text, height=200, disabled=True)
        
        st.warning("⚠️ To edit these settings, modify `config.py` file directly.")
    
    elif admin_tab == "🔑 Keywords & Taxonomy":
        st.subheader("🔑 Keywords & Taxonomy Management")
        
        # Consulting Taxonomy
        st.markdown("### Consulting Taxonomy Categories")
        for category, rules in CONSULTING_TAXONOMY.items():
            with st.expander(f"📂 {category}"):
                st.markdown("**Primary Keywords:**")
                st.code(", ".join(rules.get('primary_keywords', [])))
                
                st.markdown("**Exclude Keywords:**")
                st.code(", ".join(rules.get('exclude_keywords', [])))
                
                st.markdown("**Secondary Context:**")
                st.code(", ".join(rules.get('secondary_context', [])))
        
        st.divider()
        
        # Keyword Expansions
        st.markdown("### Keyword Expansions")
        for base_term, expansions in KEYWORD_EXPANSIONS.items():
            with st.expander(f"🔤 {base_term}"):
                st.write(", ".join(expansions))
        
        st.warning("⚠️ To edit keywords, modify `config.py` file directly.")
    
    elif admin_tab == "⚙️ Scraping Settings":
        st.subheader("⚙️ Scraping Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Max Pages", SCRAPING_CONFIG.get('max_pages', 10))
            st.metric("Retry Attempts", SCRAPING_CONFIG.get('retry_attempts', 3))
        
        with col2:
            st.metric("Rate Limit Min", f"{SCRAPING_CONFIG.get('rate_limit_min', 1)}s")
            st.metric("Rate Limit Max", f"{SCRAPING_CONFIG.get('rate_limit_max', 3)}s")
        
        with col3:
            st.metric("Retry Backoff", f"{SCRAPING_CONFIG.get('retry_backoff', 2)}x")
        
        st.divider()
        
        # Scheduler Status
        st.markdown("### Agent Scheduler")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.agent.is_running:
                st.success("✅ Scheduler is running")
                if st.button("⏸️ Stop Scheduler", type="secondary"):
                    st.session_state.agent.stop_scheduler()
                    st.rerun()
            else:
                st.info("⏸️ Scheduler is stopped")
                if st.button("▶️ Start Scheduler", type="primary"):
                    st.session_state.agent.start_scheduler()
                    st.rerun()
        
        with col2:
            st.info("📅 Daily Run: 08:00 AM\n⏰ Watchlist Check: Every 6 hours")
        
        st.divider()
        
        # API Key Status
# Page Configuration
        st.markdown("### API Configuration")
        if os.getenv('GOOGLE_API_KEY'):
            st.success("✅ Gemini API Key configured")
        else:
            st.error("❌ Gemini API Key not found")
        
        st.warning("⚠️ To edit scraping settings, modify `config.py` file directly.")
    
    elif admin_tab == "👥 Users":
        st.subheader("👥 User Management")
        st.info("Manage user accounts and admin access")
        
        # Get all users
        users = st.session_state.auth_manager.get_all_users()
        
        st.markdown(f"**Total Users:** {len(users)}")
        
        for user in users:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    admin_badge = "🛡️ Admin" if user['is_admin'] else "👤 User"
                    status_badge = "✅" if user['is_active'] else "❌"
                    st.markdown(f"**{user['username']}** {admin_badge}")
                    st.caption(f"{user['email']}")
                
                with col2:
                    st.caption(f"Created: {user['created_at'][:10] if user['created_at'] else 'N/A'}")
                    st.caption(f"Last Login: {user['last_login'][:10] if user['last_login'] else 'Never'}")
                
                with col3:
                    # Don't allow modifying own account or the main admin
                    current_user = get_current_user()
                    if user['id'] != current_user['id']:
                        if user['is_admin']:
                            if st.button("❌ Revoke Admin", key=f"revoke_{user['id']}"):
                                st.session_state.auth_manager.set_admin_status(user['id'], False)
                                st.success(f"Revoked admin from {user['username']}")
                                st.rerun()
                        else:
                            if st.button("🛡️ Grant Admin", key=f"grant_{user['id']}"):
                                st.session_state.auth_manager.set_admin_status(user['id'], True)
                                st.success(f"Granted admin to {user['username']}")
                                st.rerun()

    elif admin_tab == "📧 Email Management":
        st.subheader("📧 Email Recipient Management")
        st.info("Manage the list of team members who receive automated and manual reports.")
        
        # Add new recipient
        with st.form("add_email_form", clear_on_submit=True):
            col1, col2 = st.columns([2, 2])
            with col1:
                new_email = st.text_input("Email Address", placeholder="user@company.com")
            with col2:
                new_name = st.text_input("Name (Optional)", placeholder="John Doe")
            
            submitted = st.form_submit_button("➕ Add Recipient")
            if submitted and new_email:
                if st.session_state.db.add_recipient(new_email, new_name):
                    st.success(f"Added {new_email}")
                    st.rerun()
                else:
                    st.error("Failed to add email. It might already exist.")
        
        st.divider()
        
        # List recipients
        recipients = st.session_state.db.get_all_recipients()
        
        if not recipients:
            st.warning("No recipients configured. Emails will fall back to config file.")
        else:
            st.write(f"**Current Recipients ({len(recipients)}):**")
            
            for i, r in enumerate(recipients):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"📧 **{r['email']}**")
                with col2:
                    st.caption(f"👤 {r['name'] or 'N/A'}")
                with col3:
                    if st.button("🗑️ Remove", key=f"del_email_{i}"):
                        st.session_state.db.remove_recipient(r['email'])
                        st.rerun()
                    else:
                        st.caption("(Your account)")
                
                with col4:
                    if user['id'] != current_user['id']:
                        if user['is_active']:
                            if st.button("🚫 Deactivate", key=f"deact_{user['id']}"):
                                st.session_state.auth_manager.toggle_user_active(user['id'])
                                st.rerun()
                        else:
                            if st.button("✅ Activate", key=f"act_{user['id']}"):
                                st.session_state.auth_manager.toggle_user_active(user['id'])
                                st.rerun()
