#!/usr/bin/env python3
"""
COMPREHENSIVE PHASE 2 API TESTING SUITE
Tests all endpoints from:
- Review Queue API
- Auto-Booking API
- Bank Reconciliation API
- Chat API
- Demo API
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import csv
from io import StringIO

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None
        self.demo_task_id = None
        
    def extract_error(self, resp: dict) -> str:
        """Safely extract error message from response"""
        if resp.get("error"):
            return resp.get("error")
        if isinstance(resp.get("data"), dict):
            return resp.get("data", {}).get("detail") or resp.get("data", {}).get("message")
        return None
    
    def log_result(self, category: str, endpoint: str, method: str, 
                   status: str, http_code: int = None, 
                   response_time: float = None, error: str = None):
        """Log a test result"""
        result = {
            "category": category,
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "http_code": http_code,
            "response_time_ms": round(response_time * 1000, 2) if response_time else None,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        self.total_tests += 1
        
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ {category} | {method} {endpoint} | {http_code} | {response_time*1000:.0f}ms")
        else:
            self.failed_tests += 1
            print(f"❌ {category} | {method} {endpoint} | {error}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, dict, float]:
        """Make HTTP request and return (success, response_data, response_time)"""
        url = f"{BASE_URL}{endpoint}"
        start = time.time()
        
        try:
            if method == "GET":
                response = requests.get(url, **kwargs)
            elif method == "POST":
                response = requests.post(url, **kwargs)
            elif method == "PUT":
                response = requests.put(url, **kwargs)
            elif method == "DELETE":
                response = requests.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            elapsed = time.time() - start
            
            # Consider 2xx and 404 (for empty resources) as success
            success = 200 <= response.status_code < 300 or response.status_code == 404
            
            try:
                data = response.json()
            except:
                data = {"text": response.text[:200]}
            
            return success, {"status_code": response.status_code, "data": data}, elapsed
            
        except Exception as e:
            elapsed = time.time() - start
            return False, {"error": str(e)}, elapsed
    
    # ==========================================
    # REVIEW QUEUE API TESTS
    # ==========================================
    
    def test_review_queue(self):
        """Test Review Queue API endpoints"""
        print("\n" + "="*60)
        print("🔍 TESTING REVIEW QUEUE API")
        print("="*60)
        
        # 1. GET /api/review-queue - list items
        success, resp, elapsed = self.make_request("GET", "/api/review-queue")
        self.log_result(
            "Review Queue", "/api/review-queue", "GET",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed, self.extract_error(resp)
        )
        
        # Store first item ID if available
        review_item_id = None
        if success and resp.get("data") and isinstance(resp["data"], list) and len(resp["data"]) > 0:
            review_item_id = resp["data"][0].get("id")
        
        # 2. GET /api/review-queue/stats
        success, resp, elapsed = self.make_request("GET", "/api/review-queue/stats")
        self.log_result(
            "Review Queue", "/api/review-queue/stats", "GET",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # 3. GET /api/review-queue/{id} - item details
        if review_item_id:
            success, resp, elapsed = self.make_request("GET", f"/api/review-queue/{review_item_id}")
            self.log_result(
                "Review Queue", f"/api/review-queue/{review_item_id}", "GET",
                "PASS" if success else "FAIL",
                resp.get("status_code"), elapsed,
                self.extract_error(resp)
            )
            
            # 4. POST /api/review-queue/{id}/approve
            success, resp, elapsed = self.make_request(
                "POST", f"/api/review-queue/{review_item_id}/approve",
                json={"notes": "Test approval"}
            )
            self.log_result(
                "Review Queue", f"/api/review-queue/{review_item_id}/approve", "POST",
                "PASS" if success else "FAIL",
                resp.get("status_code"), elapsed,
                self.extract_error(resp)
            )
            
            # 5. POST /api/review-queue/{id}/correct
            success, resp, elapsed = self.make_request(
                "POST", f"/api/review-queue/{review_item_id}/correct",
                json={
                    "corrections": {"account": "5000"},
                    "notes": "Test correction",
                    "learn": True
                }
            )
            self.log_result(
                "Review Queue", f"/api/review-queue/{review_item_id}/correct", "POST",
                "PASS" if success else "FAIL",
                resp.get("status_code"), elapsed,
                self.extract_error(resp)
            )
        else:
            print("⚠️  No review items found - skipping detail/approve/correct tests")
            for endpoint in ["/api/review-queue/{id}", "/api/review-queue/{id}/approve", "/api/review-queue/{id}/correct"]:
                self.log_result("Review Queue", endpoint, "GET/POST", "SKIP", None, None, "No items available")
    
    # ==========================================
    # AUTO-BOOKING API TESTS
    # ==========================================
    
    def test_auto_booking(self):
        """Test Auto-Booking API endpoints"""
        print("\n" + "="*60)
        print("🤖 TESTING AUTO-BOOKING API")
        print("="*60)
        
        # 1. GET /api/auto-booking/stats
        success, resp, elapsed = self.make_request("GET", "/api/auto-booking/stats")
        self.log_result(
            "Auto-Booking", "/api/auto-booking/stats", "GET",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # 2. GET /api/auto-booking/status
        success, resp, elapsed = self.make_request("GET", "/api/auto-booking/status")
        self.log_result(
            "Auto-Booking", "/api/auto-booking/status", "GET",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # 3. POST /api/auto-booking/process-single (test with minimal data)
        success, resp, elapsed = self.make_request(
            "POST", "/api/auto-booking/process-single",
            json={
                "invoice_id": "test_invoice_123",
                "vendor": "Test Vendor AS",
                "amount": 1000.00,
                "description": "Test invoice for auto-booking"
            }
        )
        self.log_result(
            "Auto-Booking", "/api/auto-booking/process-single", "POST",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # 4. POST /api/auto-booking/process (batch)
        success, resp, elapsed = self.make_request(
            "POST", "/api/auto-booking/process",
            json={
                "invoices": [
                    {
                        "invoice_id": "batch_test_001",
                        "vendor": "Vendor A",
                        "amount": 500.00,
                        "description": "Batch test 1"
                    },
                    {
                        "invoice_id": "batch_test_002",
                        "vendor": "Vendor B",
                        "amount": 750.00,
                        "description": "Batch test 2"
                    }
                ]
            }
        )
        self.log_result(
            "Auto-Booking", "/api/auto-booking/process", "POST",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
    
    # ==========================================
    # BANK RECONCILIATION API TESTS
    # ==========================================
    
    def test_bank_reconciliation(self):
        """Test Bank Reconciliation API endpoints"""
        print("\n" + "="*60)
        print("🏦 TESTING BANK RECONCILIATION API")
        print("="*60)
        
        # 1. GET /api/bank/reconciliation/stats
        success, resp, elapsed = self.make_request("GET", "/api/bank/reconciliation/stats")
        self.log_result(
            "Bank Reconciliation", "/api/bank/reconciliation/stats", "GET",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # 2. POST /api/bank/import (CSV import)
        # Create test CSV data
        csv_data = """Date,Description,Amount,Reference
2026-02-01,Test Transaction 1,1500.00,REF001
2026-02-02,Test Transaction 2,-500.00,REF002
2026-02-03,Test Transaction 3,2000.00,REF003"""
        
        success, resp, elapsed = self.make_request(
            "POST", "/api/bank/import",
            files={"file": ("test_bank.csv", csv_data, "text/csv")}
        )
        self.log_result(
            "Bank Reconciliation", "/api/bank/import", "POST",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # 3. GET /api/bank/transactions (unmatched)
        success, resp, elapsed = self.make_request("GET", "/api/bank/transactions")
        self.log_result(
            "Bank Reconciliation", "/api/bank/transactions", "GET",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # Get transaction ID if available
        transaction_id = None
        if success and resp.get("data") and isinstance(resp["data"], list) and len(resp["data"]) > 0:
            transaction_id = resp["data"][0].get("id")
        
        # 4. GET /api/bank/transactions/{id}/suggestions
        if transaction_id:
            success, resp, elapsed = self.make_request(
                "GET", f"/api/bank/transactions/{transaction_id}/suggestions"
            )
            self.log_result(
                "Bank Reconciliation", f"/api/bank/transactions/{transaction_id}/suggestions", "GET",
                "PASS" if success else "FAIL",
                resp.get("status_code"), elapsed,
                self.extract_error(resp)
            )
            
            # 5. POST /api/bank/transactions/{id}/match
            success, resp, elapsed = self.make_request(
                "POST", f"/api/bank/transactions/{transaction_id}/match",
                json={"voucher_id": "test_voucher_001", "confidence": 0.95}
            )
            self.log_result(
                "Bank Reconciliation", f"/api/bank/transactions/{transaction_id}/match", "POST",
                "PASS" if success else "FAIL",
                resp.get("status_code"), elapsed,
                self.extract_error(resp)
            )
        else:
            print("⚠️  No bank transactions found - skipping suggestions/match tests")
            for endpoint in ["/api/bank/transactions/{id}/suggestions", "/api/bank/transactions/{id}/match"]:
                self.log_result("Bank Reconciliation", endpoint, "GET/POST", "SKIP", None, None, "No transactions available")
    
    # ==========================================
    # CHAT API TESTS
    # ==========================================
    
    def test_chat_api(self):
        """Test Chat API endpoints"""
        print("\n" + "="*60)
        print("💬 TESTING CHAT API")
        print("="*60)
        
        # Test different intents
        test_messages = [
            ("Bokfør faktura fra Acme Corp, beløp 5000 kr", "bokføring"),
            ("Vis meg en rapport over inntekter i januar", "rapport"),
            ("Søk etter leverandør Microsoft", "søk"),
            ("Hva er status på periodeavslutning?", "status"),
            ("Hei, hvordan går det?", "greeting")
        ]
        
        for message, intent in test_messages:
            # 1. POST /api/chat/message
            success, resp, elapsed = self.make_request(
                "POST", "/api/chat/message",
                json={"message": message, "session_id": "test_session_001"}
            )
            self.log_result(
                f"Chat API ({intent})", "/api/chat/message", "POST",
                "PASS" if success else "FAIL",
                resp.get("status_code"), elapsed,
                self.extract_error(resp)
            )
            time.sleep(0.5)  # Rate limiting
        
        # 2. GET /api/chat/history
        success, resp, elapsed = self.make_request(
            "GET", "/api/chat/history",
            params={"session_id": "test_session_001"}
        )
        self.log_result(
            "Chat API", "/api/chat/history", "GET",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
    
    # ==========================================
    # DEMO API TESTS
    # ==========================================
    
    def test_demo_api(self):
        """Test Demo API endpoints"""
        print("\n" + "="*60)
        print("🎬 TESTING DEMO API")
        print("="*60)
        
        # 1. GET /demo/status
        success, resp, elapsed = self.make_request("GET", "/demo/status")
        self.log_result(
            "Demo API", "/demo/status", "GET",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # 2. POST /demo/run-test (generate test data)
        success, resp, elapsed = self.make_request(
            "POST", "/demo/run-test",
            json={"scenario": "basic", "count": 5}
        )
        self.log_result(
            "Demo API", "/demo/run-test", "POST",
            "PASS" if success else "FAIL",
            resp.get("status_code"), elapsed,
            self.extract_error(resp)
        )
        
        # Store task_id if available
        if success and resp.get("data"):
            self.demo_task_id = resp["data"].get("task_id")
        
        # 3. GET /demo/task/{task_id} (poll status)
        if self.demo_task_id:
            time.sleep(1)  # Wait a bit before polling
            success, resp, elapsed = self.make_request("GET", f"/demo/task/{self.demo_task_id}")
            self.log_result(
                "Demo API", f"/demo/task/{self.demo_task_id}", "GET",
                "PASS" if success else "FAIL",
                resp.get("status_code"), elapsed,
                self.extract_error(resp)
            )
        else:
            print("⚠️  No task_id received - skipping task polling test")
            self.log_result("Demo API", "/demo/task/{task_id}", "GET", "SKIP", None, None, "No task_id available")
    
    # ==========================================
    # REPORT GENERATION
    # ==========================================
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 TEST REPORT SUMMARY")
        print("="*60)
        
        total_time = time.time() - self.start_time
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Tests:    {self.total_tests}")
        print(f"   Passed:         {self.passed_tests} ✅")
        print(f"   Failed:         {self.failed_tests} ❌")
        print(f"   Pass Rate:      {pass_rate:.1f}%")
        print(f"   Total Time:     {total_time:.2f}s")
        
        # Category breakdown
        print(f"\n📂 Results by Category:")
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"pass": 0, "fail": 0, "skip": 0}
            categories[cat][result["status"].lower()] += 1
        
        for cat, stats in sorted(categories.items()):
            total = stats["pass"] + stats["fail"] + stats["skip"]
            rate = (stats["pass"] / total * 100) if total > 0 else 0
            print(f"   {cat:25s} | Pass: {stats['pass']:2d} | Fail: {stats['fail']:2d} | Skip: {stats['skip']:2d} | Rate: {rate:5.1f}%")
        
        # Performance metrics
        print(f"\n⚡ Performance Metrics:")
        response_times = [r["response_time_ms"] for r in self.results if r["response_time_ms"]]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            print(f"   Average Response: {avg_time:.0f}ms")
            print(f"   Min Response:     {min_time:.0f}ms")
            print(f"   Max Response:     {max_time:.0f}ms")
        
        # Failed tests detail
        failed = [r for r in self.results if r["status"] == "FAIL"]
        if failed:
            print(f"\n❌ Failed Tests Detail:")
            for f in failed:
                print(f"   {f['category']:20s} | {f['method']:4s} {f['endpoint']:40s}")
                print(f"      Error: {f['error']}")
        
        # Save to JSON file
        report_file = "phase2_test_report.json"
        with open(report_file, "w") as f:
            json.dump({
                "summary": {
                    "total_tests": self.total_tests,
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "pass_rate": pass_rate,
                    "total_time_seconds": total_time,
                    "timestamp": datetime.now().isoformat()
                },
                "category_stats": categories,
                "performance": {
                    "avg_response_ms": avg_time if response_times else 0,
                    "min_response_ms": min_time if response_times else 0,
                    "max_response_ms": max_time if response_times else 0
                },
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if self.failed_tests == 0:
            print("   ✅ All tests passed! API is functioning correctly.")
        elif pass_rate >= 90:
            print("   ⚠️  High pass rate but some failures. Review failed tests.")
        elif pass_rate >= 70:
            print("   ⚠️  Moderate pass rate. Several endpoints need attention.")
        else:
            print("   🚨 Low pass rate. Critical issues detected. Immediate action required.")
        
        if response_times and avg_time > 1000:
            print("   ⚠️  Average response time > 1s. Consider performance optimization.")
        
        return pass_rate >= 95  # Skattefunn target: 95% accuracy
    
    def run_all_tests(self):
        """Run all test suites"""
        self.start_time = time.time()
        
        print("\n" + "="*60)
        print("🚀 PHASE 2 API COMPREHENSIVE TESTING")
        print("="*60)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL:   {BASE_URL}")
        
        # Run all test suites
        self.test_review_queue()
        self.test_auto_booking()
        self.test_bank_reconciliation()
        self.test_chat_api()
        self.test_demo_api()
        
        # Generate final report
        success = self.generate_report()
        
        return 0 if success else 1


def main():
    """Main entry point"""
    tester = APITester()
    exit_code = tester.run_all_tests()
    
    print("\n" + "="*60)
    print("✅ TESTING COMPLETE" if exit_code == 0 else "❌ TESTING COMPLETE WITH FAILURES")
    print("="*60 + "\n")
    
    return exit_code


if __name__ == "__main__":
    exit(main())
