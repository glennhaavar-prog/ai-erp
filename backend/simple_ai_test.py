#!/usr/bin/env python3
"""
Simple AI Features Test
Quick verification that all services load and can be imported
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/ai-erp/backend')

print("="*60)
print("🧪 SIMPLE AI FEATURES TEST")
print("="*60)

tests_passed = 0
tests_failed = 0

# Test 1: Import services
print("\n📦 Testing imports...")
try:
    from app.services.ai_categorization_service import AICategorizationService
    print("✅ AICategorizationService imported")
    tests_passed += 1
except Exception as e:
    print(f"❌ Failed to import AICategorizationService: {e}")
    tests_failed += 1

try:
    from app.services.anomaly_detection_service import AnomalyDetectionService
    print("✅ AnomalyDetectionService imported")
    tests_passed += 1
except Exception as e:
    print(f"❌ Failed to import AnomalyDetectionService: {e}")
    tests_failed += 1

try:
    from app.services.smart_reconciliation_service import SmartReconciliationService
    print("✅ SmartReconciliationService imported")
    tests_passed += 1
except Exception as e:
    print(f"❌ Failed to import SmartReconciliationService: {e}")
    tests_failed += 1

try:
    from app.services.payment_terms_extractor import PaymentTermsExtractor
    print("✅ PaymentTermsExtractor imported")
    tests_passed += 1
except Exception as e:
    print(f"❌ Failed to import PaymentTermsExtractor: {e}")
    tests_failed += 1

try:
    from app.services.contextual_help_service import ContextualHelpService
    print("✅ ContextualHelpService imported")
    tests_passed += 1
except Exception as e:
    print(f"❌ Failed to import ContextualHelpService: {e}")
    tests_failed += 1

# Test 2: Import API endpoints
print("\n🌐 Testing API endpoints...")
try:
    from app.api import ai_features
    print("✅ AI Features API imported")
    tests_passed += 1
except Exception as e:
    print(f"❌ Failed to import AI Features API: {e}")
    tests_failed += 1

# Test 3: Test payment terms extraction (no DB needed)
print("\n📅 Testing payment terms extraction...")
try:
    from app.services.payment_terms_extractor import PaymentTermsExtractor
    from datetime import date
    
    extractor = PaymentTermsExtractor(None)  # No DB needed for basic extraction
    
    test_cases = [
        ("30 dager netto", 30),
        ("Netto 14 dager", 14),
        ("Betales ved mottak", 0),
    ]
    
    for text, expected_days in test_cases:
        result = extractor.extract_payment_terms(text, date.today())
        if result['payment_days'] == expected_days:
            print(f"  ✅ '{text}' → {expected_days} days")
            tests_passed += 1
        else:
            print(f"  ❌ '{text}' → Expected {expected_days}, got {result['payment_days']}")
            tests_failed += 1
            
except Exception as e:
    print(f"❌ Payment terms test failed: {e}")
    tests_failed += 1

# Test 4: Test Levenshtein distance calculation
print("\n🔍 Testing text similarity...")
try:
    from app.services.smart_reconciliation_service import SmartReconciliationService
    
    service = SmartReconciliationService(None)
    
    # Test identical strings
    sim1 = service.calculate_text_similarity("Power Company AS", "Power Company AS")
    if sim1 == 1.0:
        print(f"  ✅ Identical strings: {sim1}")
        tests_passed += 1
    else:
        print(f"  ❌ Identical strings should be 1.0, got {sim1}")
        tests_failed += 1
    
    # Test similar strings
    sim2 = service.calculate_text_similarity("Power Company AS", "PowerCompany AS")
    if sim2 > 0.8:
        print(f"  ✅ Similar strings: {sim2:.2f}")
        tests_passed += 1
    else:
        print(f"  ❌ Similar strings should be >0.8, got {sim2}")
        tests_failed += 1
        
except Exception as e:
    print(f"❌ Text similarity test failed: {e}")
    tests_failed += 1

# Test 5: Test contextual help (no DB needed for defaults)
print("\n💡 Testing contextual help...")
try:
    from app.services.contextual_help_service import ContextualHelpService
    
    service = ContextualHelpService(None)
    
    # Check if default help texts exist
    if "vendor_invoice" in service.default_help_texts:
        print(f"  ✅ Default help texts loaded")
        tests_passed += 1
    else:
        print(f"  ❌ Default help texts not found")
        tests_failed += 1
    
    # Check specific field
    if "invoice_number" in service.default_help_texts.get("vendor_invoice", {}):
        help_text = service.default_help_texts["vendor_invoice"]["invoice_number"]["client"]
        print(f"  ✅ Invoice number help: {help_text[:50]}...")
        tests_passed += 1
    else:
        print(f"  ❌ Invoice number help not found")
        tests_failed += 1
        
except Exception as e:
    print(f"❌ Contextual help test failed: {e}")
    tests_failed += 1

# Summary
print("\n" + "="*60)
print(f"Tests run: {tests_passed + tests_failed}")
print(f"Passed: {tests_passed} ✅")
print(f"Failed: {tests_failed} ❌")
print("="*60)

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED!")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed")
    sys.exit(1)
