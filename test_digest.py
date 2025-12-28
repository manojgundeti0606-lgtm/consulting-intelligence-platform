"""
Test script for the new daily digest email format
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_notifier import generate_daily_digest, send_daily_digest_to_all_users

def test_new_digest():
    print("=" * 60)
    print("📧 TESTING NEW DAILY DIGEST FORMAT")
    print("=" * 60)
    
    # Sample user
    user = {
        "name": "Manoj",
        "email": "manoj@admin.com",
        "timezone": "Asia/Kolkata"
    }
    
    # Sample bids (simulating last 24 hours)
    sample_bids = [
        {
            "Bid Number": "GEM/2024/B/5123456",
            "Items": "Consulting Services for Digital Transformation Strategy",
            "Department": "Digital India Division",
            "Organisation": "Ministry of Electronics and IT",
            "End Date": "2024-12-30 18:00:00",
            "Start Date": "2024-12-27 10:00:00",
            "EMD": "1,00,000",
            "sow_summary": "Development of comprehensive digital transformation roadmap including current state assessment, technology gap analysis, and implementation strategy for modernizing citizen services."
        },
        {
            "Bid Number": "GEM/2024/B/5123789",
            "Items": "IT Infrastructure Audit and Security Assessment",
            "Department": "National Informatics Centre",
            "Organisation": "Ministry of Communications",
            "End Date": "2024-12-29 15:00:00",
            "Start Date": "2024-12-26 09:00:00",
            "EMD": "50,000",
            "sow_summary": "Complete IT infrastructure audit covering network security, data protection compliance, vulnerability assessment, and recommendations for security improvements."
        },
        {
            "Bid Number": "GEM/2024/B/5124000",
            "Items": "Project Management Consultancy for Smart City Initiative",
            "Organisation": "Ministry of Urban Development",
            "End Date": "2025-01-05 17:00:00",
            "EMD": "2,50,000",
            "sow_summary": ""  # Test empty SOW
        }
    ]
    
    # Test 1: Generate digest with bids
    print("\n1️⃣ Generating digest with 3 sample bids...")
    result = generate_daily_digest(user, sample_bids, "http://localhost:8518")
    
    print(f"\n📋 Subject: {result['email_subject']}")
    print(f"📄 HTML length: {len(result['html_body'])} chars")
    print(f"📝 Text length: {len(result['text_body'])} chars")
    
    # Check format compliance
    print("\n2️⃣ Checking format compliance...")
    
    checks = [
        ("Subject format", "3 new" in result['email_subject']),
        ("Greeting", "Hello Manoj" in result['html_body']),
        ("Bid count", "3 new bid(s)" in result['html_body']),
        ("Nearest deadline first", "2024-12-29" in result['html_body'].split("1)")[1][:100] if "1)" in result['html_body'] else False),
        ("Ministry/Organisation label", "Ministry/Organisation:" in result['html_body']),
        ("EMD field", "EMD:" in result['html_body']),
        ("Deadline field", "Deadline:" in result['html_body']),
        ("Reference field", "Reference:" in result['html_body']),
        ("Read more link", "Read more</a>" in result['html_body']),
        ("Plain text fallback", "Hello Manoj" in result['text_body']),
        ("Deep link format", "utm_source=digest" in result['html_body']),
        ("No bullets in bid", "<li>" not in result['html_body'].split("<hr")[1] if "<hr" in result['html_body'] else True),
        ("Single paragraph per bid", result['html_body'].count("<p style=") >= 4),  # Greeting + intro + bids
    ]
    
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    # Test 2: Generate digest with no bids
    print("\n3️⃣ Testing empty bids case...")
    empty_result = generate_daily_digest(user, [], "http://localhost:8518")
    
    empty_checks = [
        ("No-bids subject", "No new bids" in empty_result['email_subject']),
        ("Suggestions present", "keywords" in empty_result['html_body'].lower() or "filter" in empty_result['html_body'].lower()),
        ("Load History link", "load-history" in empty_result['html_body']),
    ]
    
    for name, passed in empty_checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    # Save samples
    print("\n4️⃣ Saving sample emails...")
    os.makedirs("test_output", exist_ok=True)
    
    with open("test_output/daily_digest_with_bids.html", "w", encoding="utf-8") as f:
        f.write(result['html_body'])
    print("   ✅ Saved: test_output/daily_digest_with_bids.html")
    
    with open("test_output/daily_digest_no_bids.html", "w", encoding="utf-8") as f:
        f.write(empty_result['html_body'])
    print("   ✅ Saved: test_output/daily_digest_no_bids.html")
    
    with open("test_output/daily_digest_plaintext.txt", "w", encoding="utf-8") as f:
        f.write(result['text_body'])
    print("   ✅ Saved: test_output/daily_digest_plaintext.txt")
    
    # Test 3: Send actual email
    print("\n5️⃣ Sending test digest email to all users...")
    send_result = send_daily_digest_to_all_users(sample_bids, "http://localhost:8518")
    
    print(f"   Sent: {send_result['sent_count']}")
    print(f"   Failed: {send_result['failed_count']}")
    if send_result['errors']:
        for err in send_result['errors']:
            print(f"   ⚠️ {err}")
    
    print("\n" + "=" * 60)
    print("✅ DAILY DIGEST TEST COMPLETE")
    print("=" * 60)
    print("\n📂 Open test_output/daily_digest_with_bids.html in browser to preview!")

if __name__ == "__main__":
    test_new_digest()
