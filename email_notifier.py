"""
Email Notification Module for Consulting Intelligence Platform
Sends daily bid digest with PDF reports attached via SMTP

Author: Manoj Gundeti
Last Updated: 2025-12-27
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def _parse_smtp_port(default: int = 587) -> int:
    """
    Safely parse SMTP_PORT from environment variable.
    Falls back to default if parsing fails or value is invalid.
    
    Args:
        default: Default port to use if parsing fails (587 for TLS)
        
    Returns:
        Valid SMTP port as integer
    """
    port_str = os.getenv("SMTP_PORT", str(default))
    
    # Check if it's a valid numeric string
    if port_str.strip().isdigit():
        port = int(port_str.strip())
        # Validate port range (1-65535)
        if 1 <= port <= 65535:
            return port
        else:
            logger.warning(
                f"SMTP_PORT '{port}' is out of valid range (1-65535). "
                f"Using default port {default}."
            )
            return default
    else:
        logger.warning(
            f"SMTP_PORT '{port_str}' is not a valid integer. "
            f"Using default port {default}."
        )
        return default


# Email Configuration - Set in .env file
EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": _parse_smtp_port(587),
    "sender_email": os.getenv("SENDER_EMAIL", ""),
    "sender_password": os.getenv("SENDER_PASSWORD", ""),  # App password for Gmail
    "recipient_emails": os.getenv("RECIPIENT_EMAILS", "").split(","),  # Comma-separated
    "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true"
}


def generate_bid_report_html(bid: Dict, analysis: Dict) -> str:
    """
    Generate an HTML report for a single bid.
    
    Args:
        bid: Bid data dictionary
        analysis: AI analysis dictionary
        
    Returns:
        HTML string
    """
    # Extract data
    bid_num = bid.get('Bid Number', 'N/A')
    items = bid.get('Items', 'N/A')
    department = bid.get('Department', 'N/A')
    end_date = bid.get('End Date', 'N/A')
    doc_link = bid.get('Document Link', '#')
    
    # Analysis data
    cfs = analysis.get('cfs', {})
    score = cfs.get('score', 0)
    verdict = cfs.get('verdict', 'N/A')
    reasoning = cfs.get('reasoning', 'No reasoning available')
    
    go_no_go = analysis.get('go_no_go', {})
    recommendation = go_no_go.get('overall_recommendation', 'N/A')
    
    exec_summary = analysis.get('executive_summary', {})
    the_ask = exec_summary.get('the_ask', 'N/A') if isinstance(exec_summary, dict) else 'N/A'
    deliverables = exec_summary.get('key_deliverables', []) if isinstance(exec_summary, dict) else []
    
    # Score color
    score_color = "#11998e" if score >= 70 else "#f5a623" if score >= 50 else "#e74c3c"
    rec_color = "#11998e" if recommendation == "GO" else "#e74c3c" if recommendation == "NO_GO" else "#f5a623"
    
    # Build deliverables list
    deliverables_html = ""
    if deliverables:
        deliverables_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
        for d in deliverables[:5]:
            deliverables_html += f"<li style='margin: 5px 0;'>{d}</li>"
        deliverables_html += "</ul>"
    else:
        deliverables_html = "<p style='color: #666;'>Not available</p>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .report {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; }}
            .header h1 {{ margin: 0 0 10px 0; font-size: 24px; }}
            .header .bid-num {{ font-size: 18px; opacity: 0.9; }}
            .content {{ padding: 30px; }}
            .score-card {{ display: inline-block; padding: 15px 25px; border-radius: 10px; text-align: center; margin: 5px; }}
            .score-card .value {{ font-size: 28px; font-weight: bold; color: white; }}
            .score-card .label {{ font-size: 12px; color: white; opacity: 0.9; margin-top: 5px; }}
            .section {{ margin: 25px 0; }}
            .section h3 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 15px; }}
            .info-row {{ display: flex; margin: 10px 0; }}
            .info-label {{ font-weight: 600; color: #555; width: 150px; }}
            .info-value {{ color: #333; flex: 1; }}
            .reasoning {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; }}
            .footer {{ background: #f8f9fa; padding: 20px 30px; text-align: center; font-size: 12px; color: #666; }}
            a {{ color: #667eea; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="report">
            <div class="header">
                <h1>📊 Consulting Intelligence Report</h1>
                <div class="bid-num">{bid_num}</div>
            </div>
            
            <div class="content">
                <div style="text-align: center; margin-bottom: 25px;">
                    <div class="score-card" style="background: {score_color};">
                        <div class="value">{score}</div>
                        <div class="label">CFS Score</div>
                    </div>
                    <div class="score-card" style="background: {rec_color};">
                        <div class="value">{recommendation}</div>
                        <div class="label">Recommendation</div>
                    </div>
                    <div class="score-card" style="background: #667eea;">
                        <div class="value">{verdict}</div>
                        <div class="label">Verdict</div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📋 Bid Details</h3>
                    <div class="info-row">
                        <div class="info-label">Bid Number:</div>
                        <div class="info-value">{bid_num}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Items/Scope:</div>
                        <div class="info-value">{items}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Department:</div>
                        <div class="info-value">{department}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">End Date:</div>
                        <div class="info-value">{end_date}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Document:</div>
                        <div class="info-value"><a href="{doc_link}" target="_blank">View Tender Document →</a></div>
                    </div>
                </div>
                
                <div class="section">
                    <h3>🎯 The Ask</h3>
                    <p style="color: #333;">{the_ask}</p>
                </div>
                
                <div class="section">
                    <h3>📦 Key Deliverables</h3>
                    {deliverables_html}
                </div>
                
                <div class="section">
                    <h3>💡 AI Reasoning</h3>
                    <div class="reasoning">
                        {reasoning}
                    </div>
                </div>
            </div>
            
            <div class="footer">
                Generated by Consulting Intelligence Platform | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    return html


def generate_full_bid_section_html(item: Dict, index: int) -> str:
    """
    Generate inline full analysis HTML for a single bid to embed in email.
    Includes SOW, CFS Scores, A&D Analysis, and all details.
    
    Args:
        item: Dict with 'bid', 'analysis', 'ad_analysis', 'sow_summary'
        index: Bid number for display
        
    Returns:
        HTML string for this bid section
    """
    bid = item.get('bid', {})
    analysis = item.get('analysis', {})
    ad_analysis = item.get('ad_analysis', {})
    sow_summary = item.get('sow_summary', 'SOW not extracted')
    
    # Basic bid info
    bid_num = bid.get('Bid Number', 'N/A')
    items = bid.get('Items', 'N/A')
    department = bid.get('Department', 'N/A')
    organisation = bid.get('Organisation', department)  # Fallback to department
    end_date = bid.get('End Date', 'N/A')
    emd = bid.get('EMD', bid.get('emd', 'N/A'))  # Get EMD value
    doc_link = bid.get('Document Link', '#')
    
    # Generate app link for Read More (opens in Load History with bid number)
    app_base_url = os.getenv('APP_URL', 'http://localhost:8518')
    read_more_link = f"{app_base_url}?page=history&bid={bid_num}"
    
    # CFS Analysis
    cfs = analysis.get('cfs', {})
    score = cfs.get('score', 0)
    verdict = cfs.get('verdict', 'N/A')
    reasoning = cfs.get('reasoning', 'No reasoning available')
    
    go_no_go = analysis.get('go_no_go', {})
    recommendation = go_no_go.get('overall_recommendation', 'N/A')
    
    exec_summary = analysis.get('executive_summary', {})
    the_ask = exec_summary.get('the_ask', 'N/A') if isinstance(exec_summary, dict) else 'N/A'
    deliverables = exec_summary.get('key_deliverables', []) if isinstance(exec_summary, dict) else []
    
    # A&D Analysis
    ad_score = ad_analysis.get('a_d_relevance_score', 0) if ad_analysis else 0
    ad_rec = ad_analysis.get('recommendation', 'N/A') if ad_analysis else 'N/A'
    ad_category = ad_analysis.get('a_d_sub_category', 'N/A') if ad_analysis else 'N/A'
    ad_confidence = ad_analysis.get('confidence', 0) if ad_analysis else 0
    ad_keywords = ad_analysis.get('matched_keywords', []) if ad_analysis else []
    
    # Risk Assessment
    risk = ad_analysis.get('risk_assessment', {}) if ad_analysis else {}
    
    # Colors
    score_color = "#11998e" if score >= 70 else "#f5a623" if score >= 50 else "#e74c3c"
    rec_color = "#11998e" if recommendation == "GO" else "#e74c3c" if recommendation == "NO_GO" else "#f5a623"
    ad_score_color = "#11998e" if ad_score >= 70 else "#f5a623" if ad_score >= 50 else "#e74c3c"
    ad_rec_color = "#11998e" if ad_rec == "PURSUE" else "#e74c3c" if ad_rec == "PASS" else "#f5a623"
    
    # Deliverables HTML
    deliverables_html = ""
    if deliverables:
        for d in deliverables[:5]:
            deliverables_html += f"<li style='margin: 5px 0; color: #333;'>{d}</li>"
    else:
        deliverables_html = "<li style='color: #666;'>Not available</li>"
    
    # Keywords HTML
    keywords_html = ", ".join(str(k) for k in ad_keywords[:10]) if ad_keywords else "None detected"
    
    # Risk HTML
    def get_risk_color(val):
        if val == "Low": return "#11998e"
        elif val == "Medium": return "#f5a623"
        elif val == "High": return "#e74c3c"
        return "#666"
    
    html = f"""
    <div style="background: white; border-radius: 16px; margin: 25px 0; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); border: 1px solid #e0e0e0;">
        <!-- Bid Header -->
        <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px;">
            <div style="font-size: 12px; opacity: 0.9; margin-bottom: 5px;">BID #{index}</div>
            <div style="font-size: 20px; font-weight: bold; margin-bottom: 8px;">{bid_num}</div>
            <div style="font-size: 14px; opacity: 0.9;">{items[:100]}{'...' if len(items) > 100 else ''}</div>
        </div>
        
        <!-- Score Cards Row -->
        <div style="display: flex; justify-content: center; gap: 15px; padding: 20px; background: #f8f9fa; flex-wrap: wrap;">
            <div style="background: {score_color}; color: white; padding: 15px 25px; border-radius: 10px; text-align: center; min-width: 80px;">
                <div style="font-size: 28px; font-weight: bold;">{score}</div>
                <div style="font-size: 11px; opacity: 0.9;">CFS Score</div>
            </div>
            <div style="background: {rec_color}; color: white; padding: 15px 25px; border-radius: 10px; text-align: center; min-width: 80px;">
                <div style="font-size: 18px; font-weight: bold;">{recommendation}</div>
                <div style="font-size: 11px; opacity: 0.9;">Recommendation</div>
            </div>
            <div style="background: {ad_score_color}; color: white; padding: 15px 25px; border-radius: 10px; text-align: center; min-width: 80px;">
                <div style="font-size: 28px; font-weight: bold;">{ad_score:.0f}</div>
                <div style="font-size: 11px; opacity: 0.9;">A&D Score</div>
            </div>
            <div style="background: {ad_rec_color}; color: white; padding: 15px 25px; border-radius: 10px; text-align: center; min-width: 80px;">
                <div style="font-size: 18px; font-weight: bold;">{ad_rec}</div>
                <div style="font-size: 11px; opacity: 0.9;">A&D Action</div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div style="padding: 25px;">
            <!-- Bid Details -->
            <div style="margin-bottom: 25px;">
                <h3 style="color: #667eea; font-size: 16px; margin: 0 0 15px 0; border-bottom: 2px solid #667eea; padding-bottom: 8px;">📋 Bid Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px 0; color: #555; width: 150px;"><strong>Ministry/Org:</strong></td><td style="color: #333;">{organisation}</td></tr>
                    <tr><td style="padding: 8px 0; color: #555;"><strong>Department:</strong></td><td style="color: #333;">{department}</td></tr>
                    <tr><td style="padding: 8px 0; color: #555;"><strong>End Date:</strong></td><td style="color: #e74c3c; font-weight: bold;">{end_date}</td></tr>
                    <tr><td style="padding: 8px 0; color: #555;"><strong>EMD Amount:</strong></td><td style="color: #333; font-weight: bold;">₹ {emd}</td></tr>
                    <tr><td style="padding: 8px 0; color: #555;"><strong>Verdict:</strong></td><td style="color: #333;">{verdict}</td></tr>
                    <tr><td style="padding: 8px 0; color: #555;"><strong>A&D Category:</strong></td><td style="color: #333;">{ad_category}</td></tr>
                    <tr><td style="padding: 8px 0; color: #555;"><strong>Document:</strong></td><td><a href="{doc_link}" style="color: #667eea;">View Tender Document →</a></td></tr>
                </table>
            </div>
            
            <!-- The Ask -->
            <div style="margin-bottom: 25px;">
                <h3 style="color: #667eea; font-size: 16px; margin: 0 0 15px 0; border-bottom: 2px solid #667eea; padding-bottom: 8px;">🎯 The Ask</h3>
                <p style="color: #333; line-height: 1.6; margin: 0;">{the_ask}</p>
            </div>
            
            <!-- Key Deliverables -->
            <div style="margin-bottom: 25px;">
                <h3 style="color: #667eea; font-size: 16px; margin: 0 0 15px 0; border-bottom: 2px solid #667eea; padding-bottom: 8px;">📦 Key Deliverables</h3>
                <ul style="margin: 0; padding-left: 20px;">{deliverables_html}</ul>
            </div>
            
            <!-- SOW Summary -->
            <div style="margin-bottom: 25px;">
                <h3 style="color: #667eea; font-size: 16px; margin: 0 0 15px 0; border-bottom: 2px solid #667eea; padding-bottom: 8px;">📋 Scope of Work Summary</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; color: #333; line-height: 1.6; max-height: 200px; overflow: hidden;">
                    {sow_summary[:1500]}{'...' if len(sow_summary) > 1500 else ''}
                </div>
            </div>
            
            <!-- AI Reasoning -->
            <div style="margin-bottom: 25px;">
                <h3 style="color: #667eea; font-size: 16px; margin: 0 0 15px 0; border-bottom: 2px solid #667eea; padding-bottom: 8px;">💡 AI Reasoning</h3>
                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; color: #333; line-height: 1.6;">
                    {reasoning}
                </div>
            </div>
            
            <!-- A&D Intelligence Section -->
            <div style="margin-bottom: 15px; background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h3 style="color: #667eea; font-size: 16px; margin: 0 0 15px 0;">📊 A&D Intelligence Analysis</h3>
                
                <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 15px;">
                    <div style="flex: 1; min-width: 100px;">
                        <div style="font-size: 11px; color: #666; text-transform: uppercase;">Confidence</div>
                        <div style="font-size: 18px; font-weight: bold; color: #333;">{ad_confidence:.0f}%</div>
                    </div>
                    <div style="flex: 1; min-width: 100px;">
                        <div style="font-size: 11px; color: #666; text-transform: uppercase;">Impl. Risk</div>
                        <div style="font-size: 14px; font-weight: bold; color: {get_risk_color(risk.get('implementation_risk', 'N/A'))};">{risk.get('implementation_risk', 'N/A')}</div>
                    </div>
                    <div style="flex: 1; min-width: 100px;">
                        <div style="font-size: 11px; color: #666; text-transform: uppercase;">Scope Creep</div>
                        <div style="font-size: 14px; font-weight: bold; color: {get_risk_color(risk.get('scope_creep_risk', 'N/A'))};">{risk.get('scope_creep_risk', 'N/A')}</div>
                    </div>
                    <div style="flex: 1; min-width: 100px;">
                        <div style="font-size: 11px; color: #666; text-transform: uppercase;">Win Prob.</div>
                        <div style="font-size: 14px; font-weight: bold; color: {get_risk_color(risk.get('win_probability', 'N/A'))};">{risk.get('win_probability', 'N/A')}</div>
                    </div>
                </div>
                
                <div>
                    <div style="font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 5px;">Matched Keywords</div>
                    <div style="font-size: 13px; color: #333;">{keywords_html}</div>
                </div>
            </div>
            
            <!-- Read More Button -->
            <div style="text-align: center; padding: 20px 0; border-top: 1px solid #e0e0e0; margin-top: 20px;">
                <a href="{read_more_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 14px 40px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                    📖 Read More in App →
                </a>
            </div>
        </div>
    </div>
    """
    return html


def generate_digest_email_html(bids_with_analysis: List[Dict]) -> str:
    """
    Generate the main digest email HTML with FULL INLINE analysis for each bid.
    
    Args:
        bids_with_analysis: List of dicts with 'bid', 'analysis', 'ad_analysis', 'sow_summary'
        
    Returns:
        HTML string for email body
    """
    date_str = datetime.now().strftime('%B %d, %Y')
    
    # Group by recommendation
    go_bids = [b for b in bids_with_analysis if b.get('analysis', {}).get('go_no_go', {}).get('overall_recommendation') == 'GO']
    maybe_bids = [b for b in bids_with_analysis if b.get('analysis', {}).get('go_no_go', {}).get('overall_recommendation') == 'MAYBE']
    nogo_bids = [b for b in bids_with_analysis if b.get('analysis', {}).get('go_no_go', {}).get('overall_recommendation') == 'NO_GO']
    
    # Generate inline reports for each bid
    go_reports = ""
    for i, item in enumerate(go_bids, 1):
        go_reports += generate_full_bid_section_html(item, i)
    
    maybe_reports = ""
    for i, item in enumerate(maybe_bids, 1):
        maybe_reports += generate_full_bid_section_html(item, i)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 40px; text-align: center; border-radius: 16px 16px 0 0; }}
            .header h1 {{ margin: 0 0 10px 0; font-size: 28px; }}
            .header .date {{ font-size: 16px; opacity: 0.9; }}
            .stats {{ display: flex; justify-content: center; gap: 20px; padding: 30px; background: white; flex-wrap: wrap; }}
            .stat-card {{ background: #f8f9fa; padding: 20px 30px; border-radius: 10px; text-align: center; min-width: 100px; }}
            .stat-value {{ font-size: 32px; font-weight: bold; }}
            .stat-label {{ font-size: 12px; color: #666; margin-top: 5px; text-transform: uppercase; }}
            .section {{ padding: 20px 0; }}
            .section-title {{ font-size: 22px; color: #333; margin: 30px 0 20px 0; padding-bottom: 10px; border-bottom: 3px solid #667eea; }}
            .footer {{ background: white; padding: 30px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 16px 16px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Daily Intelligence Digest</h1>
                <div class="date">{date_str}</div>
                <div style="margin-top: 15px; font-size: 14px;">Consulting Intelligence Platform - Full Analysis Report</div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" style="color: #11998e;">{len(go_bids)}</div>
                    <div class="stat-label">GO / Pursue</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #f5a623;">{len(maybe_bids)}</div>
                    <div class="stat-label">Evaluate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #e74c3c;">{len(nogo_bids)}</div>
                    <div class="stat-label">Pass</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #667eea;">{len(bids_with_analysis)}</div>
                    <div class="stat-label">Total Analyzed</div>
                </div>
            </div>
            
            <!-- GO Recommendations with Full Reports -->
            <div class="section">
                <h2 class="section-title">✅ GO / PURSUE Recommendations</h2>
                {go_reports if go_reports else "<p style='color: #666; text-align: center; padding: 30px;'>No GO recommendations today</p>"}
            </div>
            
            <!-- MAYBE Recommendations with Full Reports -->
            {f'''
            <div class="section">
                <h2 class="section-title">⚠️ EVALUATE Recommendations</h2>
                {maybe_reports}
            </div>
            ''' if maybe_bids else ""}
            
            <div class="footer">
                <p style="margin: 0 0 10px 0;">📊 This report includes full SOW extraction, CFS Analysis, and A&D Intelligence for each bid.</p>
                <p style="margin: 0;">Generated by <strong>Consulting Intelligence Platform</strong> | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def save_bid_report(bid: Dict, analysis: Dict, output_dir: str = "reports") -> str:
    """
    Save bid report as HTML file.
    
    Args:
        bid: Bid data
        analysis: Analysis data
        output_dir: Directory to save reports
        
    Returns:
        Path to saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    bid_num = bid.get('Bid Number', 'unknown').replace('/', '_')
    filename = f"report_{bid_num}_{datetime.now().strftime('%Y%m%d')}.html"
    filepath = os.path.join(output_dir, filename)
    
    html = generate_bid_report_html(bid, analysis)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"Saved report: {filepath}")
    return filepath


def get_all_user_emails() -> List[str]:
    """
    Get all active user emails from the database.
    
    Returns:
        List of email addresses
    """
    try:
        import sqlite3
        conn = sqlite3.connect("cip_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE is_active = 1")
        emails = [row[0] for row in cursor.fetchall()]
        conn.close()
        return emails
    except Exception as e:
        logger.warning(f"Could not get user emails from database: {e}")
        return []


def send_email_digest(
    bids_with_analysis: List[Dict],
    recipient_emails: Optional[List[str]] = None,
    subject: Optional[str] = None
) -> bool:
    """
    Send email digest with bid reports attached.
    
    Args:
        bids_with_analysis: List of {'bid': {...}, 'analysis': {...}}
        recipient_emails: Override default recipients
        subject: Custom email subject
        
    Returns:
        True if sent successfully
    """
    # Check if email is configured
    if not EMAIL_CONFIG['sender_email'] or not EMAIL_CONFIG['sender_password']:
        logger.error("Email not configured. Set SENDER_EMAIL and SENDER_PASSWORD in .env")
        return False
    
    # Get recipients: priority is provided list > database users > config defaults
    if recipient_emails:
        recipients = recipient_emails
    else:
        # Try to get all active user emails from database
        db_emails = get_all_user_emails()
        if db_emails:
            recipients = db_emails
            logger.info(f"Sending to {len(recipients)} users from database")
        else:
            # Fallback to config
            recipients = EMAIL_CONFIG['recipient_emails']
    
    recipients = [r.strip() for r in recipients if r.strip()]
    
    if not recipients:
        logger.error("No recipient emails found")
        return False
    
    # Default subject
    if not subject:
        date_str = datetime.now().strftime('%Y-%m-%d')
        go_count = len([b for b in bids_with_analysis if b.get('analysis', {}).get('go_no_go', {}).get('overall_recommendation') == 'GO'])
        subject = f"🎯 CIP Daily Digest: {go_count} GO Recommendations | {date_str}"
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        
        # Email body
        body_html = generate_digest_email_html(bids_with_analysis)
        msg.attach(MIMEText(body_html, 'html'))
        
        # Attach individual reports for GO and MAYBE recommendations
        report_dir = f"reports/{datetime.now().strftime('%Y-%m-%d')}"
        os.makedirs(report_dir, exist_ok=True)
        
        for item in bids_with_analysis:
            analysis = item.get('analysis', {})
            rec = analysis.get('go_no_go', {}).get('overall_recommendation', '')
            
            # Only attach reports for GO and MAYBE recommendations
            if rec in ['GO', 'MAYBE']:
                bid = item.get('bid', {})
                report_path = save_bid_report(bid, analysis, report_dir)
                
                with open(report_path, 'rb') as f:
                    attachment = MIMEApplication(f.read(), Name=os.path.basename(report_path))
                    attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(report_path)}"'
                    msg.attach(attachment)
                    logger.info(f"Attached report: {os.path.basename(report_path)}")
        
        # Send email
        context = ssl.create_default_context()
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls(context=context)
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.sendmail(EMAIL_CONFIG['sender_email'], recipients, msg.as_string())
        
        logger.info(f"✅ Email sent successfully to: {', '.join(recipients)}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication failed. Check your email credentials or use an App Password for Gmail.")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def generate_daily_digest(
    user: Dict,
    bids: List[Dict],
    app_base_url: str = "http://localhost:8518"
) -> Dict[str, str]:
    """
    Generate a clean, professional daily digest email with boxed/card layout.
    Uses table-based layout for email client compatibility.
    
    Args:
        user: Dict with 'name', 'email', 'timezone' (e.g., 'Asia/Kolkata')
        bids: List of bid objects with required fields
        app_base_url: Base URL for deep links
        
    Returns:
        Dict with 'email_subject', 'html_body', 'text_body'
    """
    from datetime import datetime
    import pytz
    
    user_name = user.get('name', 'User')
    user_tz_str = user.get('timezone', 'Asia/Kolkata')
    
    try:
        user_tz = pytz.timezone(user_tz_str)
    except pytz.UnknownTimeZoneError:
        user_tz = pytz.timezone('Asia/Kolkata')
    
    today = datetime.now(user_tz)
    date_formatted = today.strftime('%d %b %Y')
    
    def format_datetime(iso_str: str) -> str:
        """Convert ISO datetime to user timezone and format."""
        if not iso_str or iso_str == 'N/A':
            return 'Not specified'
        try:
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(iso_str[:19], fmt)
                    dt = pytz.UTC.localize(dt).astimezone(user_tz)
                    return dt.strftime('%d %b %Y, %I:%M %p')
                except ValueError:
                    continue
            return iso_str
        except (ValueError, AttributeError):
            return iso_str
    
    def summarize_sow(sow: str) -> str:
        """Create 35-55 word consulting-style summary."""
        if not sow or sow.strip() == '':
            return 'Not specified'
        words = sow.strip().split()
        if len(words) <= 55:
            return ' '.join(words)
        summary = ' '.join(words[:50])
        if '.' in summary:
            return summary[:summary.rfind('.')+1]
        return summary + '...'
    
    # Sort by newest published/scraped first (descending)
    def get_published_for_sort(bid):
        published = bid.get('published_at') or bid.get('Start Date') or ''
        try:
            return datetime.strptime(published[:19], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(published[:10], '%Y-%m-%d')
            except ValueError:
                return datetime.min
    
    sorted_bids = sorted(bids, key=get_published_for_sort, reverse=True)
    bid_count = len(sorted_bids)
    
    # Generate subject
    if bid_count > 0:
        email_subject = f"Daily Bid Digest ({bid_count} new) — {date_formatted}"
    else:
        email_subject = f"Daily Bid Digest — No new bids in last 24 hours ({date_formatted})"
    
    # Find nearest deadline for executive note
    nearest_deadline = 'N/A'
    if sorted_bids:
        deadlines = []
        for bid in sorted_bids:
            dl = bid.get('bid_deadline') or bid.get('End Date')
            if dl:
                deadlines.append((dl, bid))
        if deadlines:
            deadlines.sort(key=lambda x: x[0])
            nearest_deadline = format_datetime(deadlines[0][0])
    
    # Build bid boxes HTML
    bid_boxes_html = []
    bid_paragraphs_text = []
    
    for i, bid in enumerate(sorted_bids, 1):
        # Extract fields with fallbacks
        bid_id = bid.get('bid_id') or bid.get('Bid Number', '')
        title = bid.get('title') or bid.get('Items', 'Untitled Bid')
        ministry = bid.get('ministry_or_organization') or bid.get('Organisation') or bid.get('Department', 'Not specified')
        tender_id = bid.get('tender_id') or bid.get('Bid Number', 'Not specified')
        portal = bid.get('portal', 'GeM')
        published = format_datetime(bid.get('published_at') or bid.get('Start Date', ''))
        deadline = format_datetime(bid.get('bid_deadline') or bid.get('End Date', ''))
        emd = bid.get('emd_amount') or bid.get('EMD') or bid.get('emd', 'Not specified')
        sow = bid.get('sow_summary') or bid.get('sow_consulting_summary', '')
        sow_summary = summarize_sow(sow)
        other_details = bid.get('any_other_details', '')
        
        # Deep link (Streamlit uses query params on root URL)
        deep_link = f"{app_base_url}?bidId={bid_id}&utm_source=digest&utm_medium=email&utm_campaign=daily_digest"
        
        # Build other details string
        other_details_str = f"Portal: {portal}; Published: {published}"
        if other_details:
            other_details_str += f"; {other_details}"
        
        # HTML box (table-based card) - EY Color Scheme
        box_html = f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #cccccc;border-radius:8px;margin:0 0 14px 0;">
  <tr>
    <td style="padding:12px 14px;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px;background:#333333;color:#ffffff;border-radius:8px 8px 0 0;">
      <strong>{i}) Bid:</strong> {title}
    </td>
  </tr>
  <tr>
    <td style="padding:12px 14px;background:#ffffff;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="33%" valign="top" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:18px;padding-right:10px;color:#333333;">
            <strong>Bid no.:</strong> {tender_id}<br/>
            <strong>EMD:</strong> {emd}
          </td>
          <td width="34%" valign="top" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:18px;padding-right:10px;color:#333333;">
            <strong>Ministry/Organisation:</strong><br/>{ministry}
          </td>
          <td width="33%" valign="top" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:18px;color:#333333;">
            <strong>Deadline:</strong><br/><span style="color:#dc3545;font-weight:bold;">{deadline}</span>
          </td>
        </tr>
      </table>
      <div style="height:10px;line-height:10px;">&nbsp;</div>
      <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:18px;color:#999999;">
        <strong style="color:#333333;">Other details:</strong> {other_details_str}
      </div>
      <div style="height:10px;line-height:10px;">&nbsp;</div>
      <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:18px;color:#333333;">
        <strong>SOW summary:</strong> {sow_summary}
      </div>
      <div style="height:12px;line-height:12px;">&nbsp;</div>
      <table role="presentation" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td bgcolor="#ffe600" style="border-radius:4px;">
            <a href="{deep_link}" style="display:inline-block;padding:10px 18px;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#333333;text-decoration:none;font-weight:bold;">
              Read more →
            </a>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>'''
        bid_boxes_html.append(box_html)
        
        # Plain text paragraph
        text_para = f"""{i}) Bid: {title}
   Bid no.: {tender_id} | EMD: {emd}
   Ministry/Organisation: {ministry}
   Deadline: {deadline}
   Other details: {other_details_str}
   SOW summary: {sow_summary}
   Read more: {deep_link}
"""
        bid_paragraphs_text.append(text_para)
    
    # Build HTML body
    if bid_count > 0:
        html_body = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family:Arial,Helvetica,sans-serif;margin:0;padding:20px;background:#f5f5f5;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:100%;background:#ffffff;border-radius:8px;">
          <tr>
            <td style="padding:25px;">
              <p style="margin:0 0 20px 0;font-size:16px;color:#333;">Hello {user_name},</p>
              
              <p style="margin:0 0 20px 0;font-size:14px;color:#555;line-height:1.6;">
                We found <strong>{bid_count} new bid(s)</strong> in the last 24 hours. 
                The nearest deadline is <strong style="color:#e74c3c;">{nearest_deadline}</strong>. 
                Open Load History in the app for full details and analysis.
              </p>
              
              <div style="height:1px;background:#eee;margin:20px 0;"></div>
              
              {''.join(bid_boxes_html)}
              
              <div style="height:1px;background:#eee;margin:20px 0;"></div>
              
              <p style="margin:0;font-size:12px;color:#888;text-align:center;">
                Consulting Intelligence Platform — Daily Digest<br/>
                <a href="{app_base_url}" style="color:#1f6feb;">Open App</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>'''
    else:
        # No bids case
        html_body = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family:Arial,Helvetica,sans-serif;margin:0;padding:20px;background:#f5f5f5;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:100%;background:#ffffff;border-radius:8px;">
          <tr>
            <td style="padding:25px;">
              <p style="margin:0 0 20px 0;font-size:16px;color:#333;">Hello {user_name},</p>
              
              <p style="margin:0 0 15px 0;font-size:14px;color:#555;line-height:1.6;">
                No new bids were scraped in the last 24 hours matching your current filters. 
                This may happen during weekends or holidays.
              </p>
              
              <p style="margin:0 0 20px 0;font-size:14px;color:#555;line-height:1.6;">
                You can review your keywords, ministries, or filter settings in 
                <a href="{app_base_url}/load-history" style="color:#1f6feb;font-weight:bold;">Load History</a> 
                to adjust your preferences.
              </p>
              
              <div style="height:1px;background:#eee;margin:20px 0;"></div>
              
              <p style="margin:0;font-size:12px;color:#888;text-align:center;">
                Consulting Intelligence Platform — Daily Digest<br/>
                <a href="{app_base_url}" style="color:#1f6feb;">Open App</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>'''
    
    # Build plain text body
    if bid_count > 0:
        text_body = f"""Hello {user_name},

We found {bid_count} new bid(s) in the last 24 hours. The nearest deadline is {nearest_deadline}. Open Load History in the app for full details and analysis.

{'=' * 60}

{chr(10).join(bid_paragraphs_text)}
{'=' * 60}

Consulting Intelligence Platform — Daily Digest
{app_base_url}
"""
    else:
        text_body = f"""Hello {user_name},

No new bids were scraped in the last 24 hours matching your current filters. This may happen during weekends or holidays.

You can review your keywords, ministries, or filter settings in Load History to adjust your preferences: {app_base_url}/load-history

{'=' * 60}

Consulting Intelligence Platform — Daily Digest
{app_base_url}
"""
    
    return {
        "email_subject": email_subject,
        "html_body": html_body,
        "text_body": text_body
    }


def send_daily_digest_to_all_users(bids: List[Dict], app_base_url: str = "http://localhost:8518") -> Dict:
    """
    Send daily digest email to all active users in the database.
    
    Args:
        bids: List of bid objects from last 24 hours
        app_base_url: Base URL for deep links
        
    Returns:
        Dict with 'success', 'sent_count', 'failed_count', 'errors'
    """
    import sqlite3
    
    results = {
        "success": True,
        "sent_count": 0,
        "failed_count": 0,
        "errors": []
    }
    
    # Check email configuration
    if not EMAIL_CONFIG['sender_email'] or not EMAIL_CONFIG['sender_password']:
        results["success"] = False
        results["errors"].append("Email not configured")
        return results
    
    # Get all active users from database
    try:
        conn = sqlite3.connect("cip_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, email FROM users WHERE is_active = 1")
        users = [{"name": row[0], "email": row[1], "timezone": "Asia/Kolkata"} for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Database error: {str(e)}")
        return results
    
    if not users:
        results["errors"].append("No active users found")
        return results
    
    logger.info(f"Sending daily digest to {len(users)} users with {len(bids)} bids")
    
    # Send to each user
    for user in users:
        try:
            # Generate personalized email
            email_content = generate_daily_digest(user, bids, app_base_url)
            
            # Create message with both HTML and plain text
            msg = MIMEMultipart('alternative')
            msg['From'] = EMAIL_CONFIG['sender_email']
            msg['To'] = user['email']
            msg['Subject'] = email_content['email_subject']
            
            # Attach plain text first, then HTML (email clients prefer last)
            msg.attach(MIMEText(email_content['text_body'], 'plain'))
            msg.attach(MIMEText(email_content['html_body'], 'html'))
            
            # Send
            context = ssl.create_default_context()
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls(context=context)
                server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
                server.sendmail(EMAIL_CONFIG['sender_email'], user['email'], msg.as_string())
            
            logger.info(f"✅ Sent digest to {user['email']}")
            results["sent_count"] += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to send to {user['email']}: {str(e)}")
            results["failed_count"] += 1
            results["errors"].append(f"{user['email']}: {str(e)[:50]}")
    
    return results


def test_email_connection() -> bool:
    """
    Test SMTP connection without sending an email.
    
    Returns:
        True if connection successful
    """
    if not EMAIL_CONFIG['sender_email'] or not EMAIL_CONFIG['sender_password']:
        logger.error("Email not configured")
        return False
    
    try:
        context = ssl.create_default_context()
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls(context=context)
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            logger.info("✅ SMTP connection test successful!")
            return True
            
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Authentication failed. For Gmail, use an App Password.")
        return False
    except Exception as e:
        logger.error(f"❌ Connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the module
    print("Testing Email Notifier...")
    
    # Test SMTP connection
    if test_email_connection():
        print("SMTP connection successful!")
    else:
        print("SMTP connection failed. Check your .env configuration:")
        print("  SMTP_SERVER=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SENDER_EMAIL=your-email@gmail.com")
        print("  SENDER_PASSWORD=your-app-password")
        print("  RECIPIENT_EMAILS=recipient1@example.com,recipient2@example.com")
        print("  EMAIL_ENABLED=true")

