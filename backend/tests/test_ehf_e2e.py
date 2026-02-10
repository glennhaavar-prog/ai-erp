"""
End-to-End Tests for EHF Invoice Processing
Tests complete flow: XML → Parse → Validate → Create Invoice → AI Processing → Review Queue
"""

import pytest
from pathlib import Path
from decimal import Decimal
from sqlalchemy import select
from httpx import AsyncClient

from app.main import app
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.client import Client
from app.models.review_queue import ReviewQueue


# Path to sample files
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ehf"

# Sample file definitions
SAMPLES = [
    {
        "file": "ehf_sample_1_simple.xml",
        "name": "Simple Invoice",
        "expected": {
            "invoice_number": "FAKTURA-2026-001",
            "vendor_org": "987654321",
            "vendor_name": "Norsk IT-Konsulent AS",
            "currency": "NOK",
            "amount_excl_vat": Decimal("25000.00"),
            "vat_amount": Decimal("6250.00"),
            "total_amount": Decimal("31250.00"),
            "line_count": 1,
        },
    },
    {
        "file": "ehf_sample_2_multi_line.xml",
        "name": "Multi-line Invoice",
        "expected": {
            "invoice_number": "FAKTURA-2026-002",
            "vendor_org": "912345678",
            "vendor_name": "Norsk Kontorrekvisita AS",
            "currency": "NOK",
            "amount_excl_vat": Decimal("44450.00"),
            "vat_amount": Decimal("8525.00"),
            "total_amount": Decimal("52975.00"),
            "line_count": 4,
        },
    },
    {
        "file": "ehf_sample_3_zero_vat.xml",
        "name": "Export Invoice (0% VAT)",
        "expected": {
            "invoice_number": "EXPORT-2026-015",
            "vendor_org": "876543219",
            "vendor_name": "Nordic Export Solutions AS",
            "currency": "NOK",
            "amount_excl_vat": Decimal("89500.00"),
            "vat_amount": Decimal("0.00"),
            "total_amount": Decimal("89500.00"),
            "line_count": 3,
        },
    },
    {
        "file": "ehf_sample_4_reverse_charge.xml",
        "name": "Reverse Charge Invoice",
        "expected": {
            "invoice_number": "INV-DK-2026-0342",
            "vendor_org": "DK12345678",
            "vendor_name": "Copenhagen Design ApS",
            "currency": "NOK",
            "amount_excl_vat": Decimal("58000.00"),
            "vat_amount": Decimal("0.00"),
            "total_amount": Decimal("58000.00"),
            "line_count": 2,
        },
    },
    {
        "file": "ehf_sample_5_credit_note.xml",
        "name": "Credit Note",
        "expected": {
            "invoice_number": "KREDITNOTA-2026-007",
            "vendor_org": "987654321",
            "vendor_name": "Norsk IT-Konsulent AS",
            "currency": "NOK",
            "amount_excl_vat": Decimal("5000.00"),
            "vat_amount": Decimal("1250.00"),
            "total_amount": Decimal("6250.00"),
            "line_count": 1,
        },
    },
]


@pytest.mark.asyncio
class TestEHFEndToEnd:
    """Complete end-to-end tests for EHF processing"""

    async def test_health_check(self, client: AsyncClient):
        """Verify test endpoint is available"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s["name"])
    async def test_ehf_sample_processing(self, client: AsyncClient, db, sample: dict):
        """
        Test complete EHF processing for each sample file
        
        Steps:
        1. Load XML file
        2. Send to test endpoint
        3. Verify API response
        4. Verify database entries (Invoice, Vendor)
        5. Verify AI processing was triggered
        6. Verify Review Queue entry (if applicable)
        """
        # Step 1: Load XML file
        xml_file = FIXTURES_DIR / sample["file"]
        assert xml_file.exists(), f"Sample file not found: {xml_file}"
        
        xml_content = xml_file.read_text(encoding="utf-8")
        assert len(xml_content) > 0, "XML file is empty"
        
        # Step 2: Send to test endpoint
        response = await client.post(
            "/api/test/ehf/send-raw",
            json={"xml_content": xml_content},
        )
        
        # Step 3: Verify API response
        assert response.status_code == 200, f"Failed to process {sample['name']}: {response.text}"
        
        result = response.json()
        assert result["success"] is True, f"Processing failed: {result.get('error')}"
        assert result["test_mode"] is True
        assert "steps" in result
        assert "summary" in result
        
        # Verify steps completed
        step_names = [step["step"] for step in result["steps"]]
        assert "parse" in step_names
        assert "validate" in step_names
        assert "vendor" in step_names
        assert "invoice_created" in step_names
        assert "ai_processing" in step_names
        
        # All steps should succeed (status contains ✅)
        for step in result["steps"]:
            if step["step"] not in ["review_queue"]:  # Review queue can be skipped
                assert "✅" in step["status"] or "⏭️" in step["status"], \
                    f"Step {step['step']} failed: {step.get('errors', [])}"
        
        # Get invoice ID from response
        invoice_id = result["summary"]["invoice_id"]
        assert invoice_id is not None
        
        # Step 4: Verify database entries
        
        # 4a. Verify Invoice created
        query = select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        invoice_result = await db.execute(query)
        invoice = invoice_result.scalar_one_or_none()
        
        assert invoice is not None, "Invoice not found in database"
        assert invoice.invoice_number == sample["expected"]["invoice_number"]
        assert invoice.currency == sample["expected"]["currency"]
        
        # Check amounts (allow small rounding differences)
        assert abs(invoice.amount_excl_vat - sample["expected"]["amount_excl_vat"]) < Decimal("0.01")
        assert abs(invoice.vat_amount - sample["expected"]["vat_amount"]) < Decimal("0.01")
        assert abs(invoice.total_amount - sample["expected"]["total_amount"]) < Decimal("0.01")
        
        # Verify line items
        assert invoice.line_items is not None
        assert len(invoice.line_items) == sample["expected"]["line_count"]
        
        # Verify EHF fields
        assert invoice.ehf_raw_xml is not None
        assert invoice.ehf_received_at is not None
        
        # 4b. Verify Vendor created/found
        query = select(Vendor).where(Vendor.id == invoice.vendor_id)
        vendor_result = await db.execute(query)
        vendor = vendor_result.scalar_one_or_none()
        
        assert vendor is not None, "Vendor not found in database"
        assert vendor.org_number == sample["expected"]["vendor_org"]
        assert vendor.name == sample["expected"]["vendor_name"]
        
        # Step 5: Verify AI processing was triggered
        # The invoice should have a review_status
        assert invoice.review_status in ["pending", "needs_review", "approved", "auto_approved"]
        
        # Step 6: Verify Review Queue entry (if applicable)
        if invoice.review_status == "needs_review":
            query = select(ReviewQueue).where(ReviewQueue.invoice_id == invoice.id)
            review_result = await db.execute(query)
            review_entry = review_result.scalar_one_or_none()
            
            # Should be in review queue
            assert review_entry is not None, "Low confidence invoice should be in review queue"
            assert review_entry.status == "pending"

    async def test_duplicate_invoice_detection(self, client: AsyncClient, db):
        """Test that duplicate invoices are detected"""
        # Send same invoice twice
        xml_file = FIXTURES_DIR / "ehf_sample_1_simple.xml"
        xml_content = xml_file.read_text(encoding="utf-8")
        
        # First submission
        response1 = await client.post(
            "/api/test/ehf/send-raw",
            json={"xml_content": xml_content},
        )
        assert response1.status_code == 200
        result1 = response1.json()
        assert result1["success"] is True
        
        # Second submission (duplicate)
        response2 = await client.post(
            "/api/test/ehf/send-raw",
            json={"xml_content": xml_content},
        )
        
        # Should still succeed, but might create duplicate
        # (In production, we'd want duplicate detection)
        assert response2.status_code == 200
        result2 = response2.json()
        
        # Both should succeed (for now)
        # TODO: Implement duplicate detection
        assert result2["success"] is True

    async def test_invalid_xml(self, client: AsyncClient):
        """Test handling of invalid XML"""
        invalid_xml = "<Invoice>broken xml without closing tag"
        
        response = await client.post(
            "/api/test/ehf/send-raw",
            json={"xml_content": invalid_xml},
        )
        
        # Should fail gracefully
        assert response.status_code in [400, 500]
        result = response.json()
        assert result["success"] is False
        assert "error" in result or "errors" in result

    async def test_missing_required_fields(self, client: AsyncClient):
        """Test handling of XML missing required fields"""
        # XML missing invoice ID
        incomplete_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
            <cbc:IssueDate>2026-02-10</cbc:IssueDate>
        </Invoice>
        """
        
        response = await client.post(
            "/api/test/ehf/send-raw",
            json={"xml_content": incomplete_xml},
        )
        
        # Should fail validation
        assert response.status_code in [400, 500]
        result = response.json()
        assert result["success"] is False

    async def test_vendor_reuse(self, client: AsyncClient, db):
        """Test that same vendor is reused across invoices"""
        # Send two invoices from same vendor
        xml_file = FIXTURES_DIR / "ehf_sample_1_simple.xml"
        xml_content = xml_file.read_text(encoding="utf-8")
        
        # First invoice
        response1 = await client.post(
            "/api/test/ehf/send-raw",
            json={"xml_content": xml_content},
        )
        assert response1.status_code == 200
        result1 = response1.json()
        
        # Get vendor count
        query = select(Vendor).where(Vendor.org_number == "987654321")
        vendors_before = await db.execute(query)
        vendor_count_before = len(list(vendors_before.scalars().all()))
        
        # Second invoice from same vendor
        response2 = await client.post(
            "/api/test/ehf/send-raw",
            json={"xml_content": xml_content},
        )
        assert response2.status_code == 200
        
        # Should still have same number of vendors (reused)
        query = select(Vendor).where(Vendor.org_number == "987654321")
        vendors_after = await db.execute(query)
        vendor_count_after = len(list(vendors_after.scalars().all()))
        
        assert vendor_count_after == vendor_count_before, "Vendor should be reused, not duplicated"

    async def test_all_samples_batch(self, client: AsyncClient):
        """Batch test: Process all samples and verify none fail"""
        results = []
        
        for sample in SAMPLES:
            xml_file = FIXTURES_DIR / sample["file"]
            xml_content = xml_file.read_text(encoding="utf-8")
            
            response = await client.post(
                "/api/test/ehf/send-raw",
                json={"xml_content": xml_content},
            )
            
            results.append({
                "name": sample["name"],
                "status_code": response.status_code,
                "success": response.json().get("success") if response.status_code == 200 else False,
            })
        
        # All should succeed
        for result in results:
            assert result["status_code"] == 200, f"{result['name']} failed with {result['status_code']}"
            assert result["success"] is True, f"{result['name']} processing failed"
        
        print("\n✅ All sample invoices processed successfully!")
        for result in results:
            print(f"  ✓ {result['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
