"""Test the pre-filter for excluding non-consulting bids"""
from intent_scorer import IntentDrivenScorer

# Test pre-filter with sample bids
scorer = IntentDrivenScorer()

# Test bids - mix of consulting and non-consulting  
test_bids = [
    # Should PASS - Clear consulting signals
    {'Items': 'Consulting Services for Digital Transformation', 'Department': 'MEITY'},
    {'Items': 'PMU Services for Smart City Project', 'Department': 'MoHUA'},
    {'Items': 'Advisory Services for E-Governance Implementation', 'Department': 'NIC'},
    {'Items': 'Feasibility Study for Metro Rail Extension', 'Department': 'DMRC'},
    {'Items': 'Third Party Quality Assurance for Highway Project', 'Department': 'NHAI'},
    {'Items': 'Selection of Agency for Baseline Survey', 'Department': 'Ministry of Rural Development'},
    
    # Should FAIL - Clear procurement/supplies
    {'Items': 'Supply of Apixaban 2.5mg Tablets', 'Department': 'Ministry of Health'},
    {'Items': 'Annual Maintenance Contract for UPS', 'Department': 'Ministry of Railways'},
    {'Items': 'Supply of Furniture and Office Equipment', 'Department': 'Ministry of Commerce'},
    {'Items': 'Supply of medicines and pharmaceutical drugs', 'Department': 'AIIMS'},
    {'Items': 'Housekeeping and Security Services', 'Department': 'RBI'},
    {'Items': 'Procurement of Desktop Computers and Laptops', 'Department': 'DoT'},
    
    # Should FAIL - Generic without consulting signals
    {'Items': 'Books and Reference Materials for Library', 'Department': 'UGC'},
    {'Items': 'Networking Equipment for Data Center', 'Department': 'NIC'},
    {'Items': 'Air Conditioning System Installation', 'Department': 'CPWD'},
]

print('Testing STRICT pre-filter...')
print('='*60)
passed = 0
failed = 0
for bid in test_bids:
    result = scorer.quick_prefilter(bid)
    status = '✅ PASS' if result else '❌ FAIL'
    if result:
        passed += 1
    else:
        failed += 1
    title = bid['Items'][:50]
    print(f'{status}: {title}')

print('='*60)
print(f'Results: {passed} passed, {failed} filtered out')
