"""
Test script for email notification functionality
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from email_notifier import (
    generate_full_bid_section_html,
    generate_digest_email_html,
    get_all_user_emails,
    send_email_digest,
    EMAIL_CONFIG
)

def test_email_feature():
    print("=" * 60)
    print("📧 EMAIL FEATURE TEST")
    print("=" * 60)
    
    # Test 1: Check email configuration
    print("\n1️⃣ Checking Email Configuration...")
    print(f"   SMTP Server: {EMAIL_CONFIG['smtp_server']}")
    print(f"   SMTP Port: {EMAIL_CONFIG['smtp_port']}")
    print(f"   Sender Email: {EMAIL_CONFIG['sender_email'] or '❌ NOT SET'}")
    print(f"   Password Set: {'✅ YES' if EMAIL_CONFIG['sender_password'] else '❌ NO'}")
    print(f"   Email Enabled: {'✅ YES' if EMAIL_CONFIG['enabled'] else '❌ NO'}")
    
    # Test 2: Get user emails from database
    print("\n2️⃣ Getting User Emails from Database...")
    user_emails = get_all_user_emails()
    if user_emails:
        print(f"   ✅ Found {len(user_emails)} active users:")
        for email in user_emails:
            print(f"      - {email}")
    else:
        print("   ⚠️ No users found in database")
    
    # Test 3: Generate sample bid HTML
    print("\n3️⃣ Testing HTML Generation...")
    
    sample_bid = {
        "Bid Number": "GEM/2024/B/TEST123",
        "Items": "Consulting Services for IT Strategy and Digital Transformation",
        "Department": "Ministry of Electronics and IT",
        "Organisation": "National Informatics Centre",
        "End Date": "2024-12-31 18:00",
        "EMD": "50,000",
        "Document Link": "https://bidplus.gem.gov.in/bid/TEST123"
    }
    
    sample_analysis = {
        "cfs": {
            "score": 85,
            "verdict": "Excellent Fit",
            "reasoning": "This bid aligns well with our consulting expertise in IT strategy and digital transformation."
        },
        "go_no_go": {
            "overall_recommendation": "GO"
        },
        "executive_summary": {
            "the_ask": "Development of comprehensive IT strategy roadmap",
            "key_deliverables": [
                "Current state assessment",
                "Gap analysis report",
                "Target architecture design",
                "Implementation roadmap"
            ]
        }
    }
    
    sample_ad_analysis = {
        "a_d_relevance_score": 78,
        "recommendation": "PURSUE",
        "a_d_sub_category": "Defense IT",
        "confidence": 85,
        "matched_keywords": ["IT Strategy", "Digital", "Government"],
        "risk_assessment": {
            "implementation_risk": "Medium",
            "scope_creep_risk": "Low",
            "win_probability": "High"
        }
    }
    
    sample_sow = "This consulting engagement requires the development of a comprehensive IT strategy..."
    
    # Generate HTML for single bid
    bid_html = generate_full_bid_section_html({
        "bid": sample_bid,
        "analysis": sample_analysis,
        "ad_analysis": sample_ad_analysis,
        "sow_summary": sample_sow
    }, 1)
    
    print(f"   ✅ Generated single bid HTML: {len(bid_html)} chars")
    
    # Check for key elements
    checks = [
        ("EMD Amount", "₹ 50,000" in bid_html),
        ("Ministry/Org", "National Informatics Centre" in bid_html or "Ministry" in bid_html),
        ("Read More Button", "Read More in App" in bid_html),
        ("CFS Score", "85" in bid_html),
        ("A&D Score", "78" in bid_html),
    ]
    
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}: {'Found' if passed else 'MISSING'}")
    
    # Test 4: Generate full digest
    print("\n4️⃣ Testing Full Digest Generation...")
    sample_bids = [
        {"bid": sample_bid, "analysis": sample_analysis, "ad_analysis": sample_ad_analysis, "sow_summary": sample_sow}
    ]
    
    digest_html = generate_digest_email_html(sample_bids)
    print(f"   ✅ Generated digest HTML: {len(digest_html)} chars")
    
    # Save sample HTML for preview
    print("\n5️⃣ Saving Sample Email for Preview...")
    os.makedirs("test_output", exist_ok=True)
    with open("test_output/sample_email.html", "w", encoding="utf-8") as f:
        f.write(digest_html)
    print(f"   ✅ Saved to: test_output/sample_email.html")
    print(f"   📂 Open this file in a browser to preview the email!")
    
    # Test 5: Attempt to send test email (if configured)
    print("\n6️⃣ Testing Email Sending...")
    if EMAIL_CONFIG['sender_email'] and EMAIL_CONFIG['sender_password']:
        print(f"   📤 Attempting to send test email...")
        try:
            success = send_email_digest(
                sample_bids,
                subject="🧪 TEST: CIP Email Feature Test"
            )
            if success:
                print("   ✅ Test email sent successfully!")
            else:
                print("   ❌ Failed to send test email")
        except Exception as e:
            print(f"   ❌ Error sending email: {str(e)[:100]}")
    else:
        print("   ⚠️ Email not configured - skipping send test")
        print("   💡 Set SENDER_EMAIL and SENDER_PASSWORD in .env to enable")
    
    print("\n" + "=" * 60)
    print("✅ EMAIL FEATURE TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_email_feature()
