#!/usr/bin/env python3
"""
Quick verification script for Phase 2 bug fixes
Tests without requiring full app initialization
"""

import sys
import ast
import re

def verify_enum_fix():
    """Verify SQL enum bug is fixed in review_queue.py"""
    print("\n🔍 Verifying Fix #1: SQL Enum Bug...")
    
    with open('app/api/routes/review_queue.py', 'r') as f:
        content = f.read()
    
    # Check that we're using ReviewStatus enums, not strings
    issues = []
    
    if "ReviewQueue.status == 'pending'" in content:
        issues.append("Found string comparison 'pending' instead of ReviewStatus.PENDING")
    
    if "ReviewQueue.status == 'approved'" in content:
        issues.append("Found string comparison 'approved' instead of ReviewStatus.APPROVED")
    
    if "ReviewQueue.status == 'corrected'" in content:
        issues.append("Found string comparison 'corrected' instead of ReviewStatus.CORRECTED")
    
    # Verify the correct enum usage exists
    if "ReviewQueue.status == ReviewStatus.PENDING" not in content:
        issues.append("Missing ReviewStatus.PENDING enum usage")
    
    if "ReviewQueue.status == ReviewStatus.APPROVED" not in content:
        issues.append("Missing ReviewStatus.APPROVED enum usage")
    
    if "ReviewQueue.status == ReviewStatus.CORRECTED" not in content:
        issues.append("Missing ReviewStatus.CORRECTED enum usage")
    
    if issues:
        print("❌ FAIL: SQL Enum Bug NOT fixed!")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ PASS: SQL queries now use proper enum comparisons")
        print("  - ReviewStatus.PENDING ✓")
        print("  - ReviewStatus.APPROVED ✓")
        print("  - ReviewStatus.CORRECTED ✓")
        return True


def verify_route_order():
    """Verify /stats route comes before /{item_id} route"""
    print("\n🔍 Verifying Fix #2: Route Order...")
    
    with open('app/api/routes/review_queue.py', 'r') as f:
        lines = f.readlines()
    
    stats_line = None
    item_id_line = None
    
    for i, line in enumerate(lines):
        if '@router.get("/stats")' in line:
            stats_line = i
        if '@router.get("/{item_id}")' in line:
            item_id_line = i
    
    if stats_line is None:
        print("❌ FAIL: /stats route not found")
        return False
    
    if item_id_line is None:
        print("❌ FAIL: /{item_id} route not found")
        return False
    
    if stats_line < item_id_line:
        print(f"✅ PASS: /stats route (line {stats_line}) comes before /{'{item_id}'} route (line {item_id_line})")
        return True
    else:
        print(f"❌ FAIL: /{'{item_id}'} route (line {item_id_line}) comes before /stats route (line {stats_line})")
        return False


def verify_auto_booking_registered():
    """Verify auto_booking router is registered in main.py"""
    print("\n🔍 Verifying Fix #3: Auto-Booking Router Registration...")
    
    with open('app/main.py', 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check import
    if 'auto_booking' not in content:
        issues.append("auto_booking not imported")
    elif re.search(r'from app\.api\.routes import.*auto_booking', content):
        print("  ✓ auto_booking imported in routes")
    else:
        issues.append("auto_booking not in routes import")
    
    # Check router registration
    if 'app.include_router(auto_booking.router)' not in content:
        issues.append("auto_booking.router not registered with app.include_router()")
    else:
        print("  ✓ auto_booking.router registered")
    
    if issues:
        print("❌ FAIL: Auto-Booking Router NOT properly registered!")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ PASS: Auto-booking router properly imported and registered")
        return True


def verify_imports():
    """Verify code can be imported without errors"""
    print("\n🔍 Verifying Imports...")
    
    try:
        from app.api.routes import review_queue, auto_booking
        print("✅ PASS: review_queue module imports successfully")
        print("✅ PASS: auto_booking module imports successfully")
        
        print(f"  - review_queue router: {review_queue.router.prefix}")
        print(f"  - auto_booking router: {auto_booking.router.prefix}")
        
        # Count routes
        rq_routes = len([r for r in review_queue.router.routes])
        ab_routes = len([r for r in auto_booking.router.routes])
        
        print(f"  - review_queue has {rq_routes} routes")
        print(f"  - auto_booking has {ab_routes} routes")
        
        return True
    except Exception as e:
        print(f"❌ FAIL: Import error: {e}")
        return False


def verify_all_endpoints():
    """List all available endpoints"""
    print("\n📋 Listing All Endpoints...")
    
    try:
        from app.api.routes import review_queue, auto_booking
        
        print("\n=== REVIEW QUEUE ENDPOINTS ===")
        for route in review_queue.router.routes:
            methods = ', '.join(route.methods)
            # Remove duplicate prefix
            path = route.path.replace('/api/review-queue', '')
            print(f"  {methods:6} {review_queue.router.prefix}{path}")
        
        print("\n=== AUTO-BOOKING ENDPOINTS ===")
        for route in auto_booking.router.routes:
            methods = ', '.join(route.methods)
            # Remove duplicate prefix
            path = route.path.replace('/api/auto-booking', '')
            print(f"  {methods:6} {auto_booking.router.prefix}{path}")
        
        total_routes = len(review_queue.router.routes) + len(auto_booking.router.routes)
        print(f"\n✅ Total endpoints verified: {total_routes}")
        
        return True
    except Exception as e:
        print(f"❌ FAIL: Could not list endpoints: {e}")
        return False


def main():
    print("=" * 70)
    print("🧪 PHASE 2 BUG FIX VERIFICATION")
    print("=" * 70)
    
    results = []
    
    # Run all verifications
    results.append(("SQL Enum Fix", verify_enum_fix()))
    results.append(("Route Order", verify_route_order()))
    results.append(("Auto-Booking Registration", verify_auto_booking_registered()))
    results.append(("Module Imports", verify_imports()))
    results.append(("Endpoint Listing", verify_all_endpoints()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL FIXES VERIFIED SUCCESSFULLY!")
        print("=" * 70)
        print("\n✅ Ready for production testing")
        print("✅ All 3 critical bugs fixed:")
        print("   1. SQL enum comparisons corrected")
        print("   2. Route order verified (no collision)")
        print("   3. Auto-booking endpoints accessible")
        return 0
    else:
        print("⚠️  SOME VERIFICATIONS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
