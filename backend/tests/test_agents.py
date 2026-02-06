"""
Tests for Multi-Agent System

Tests both with mocks (no database required) and with real database.
"""
import pytest
import asyncio
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.agents.orchestrator import OrchestratorAgent
from app.agents.invoice_parser_agent import InvoiceParserAgent
from app.agents.bookkeeping_agent import BookkeepingAgent
from app.agents.learning_agent import LearningAgent
from app.models.agent_event import AgentEvent
from app.models.agent_task import AgentTask
from app.models.vendor_invoice import VendorInvoice
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine


class TestOrchestratorMocked:
    """Test orchestrator with mocks (no database)"""
    
    @pytest.mark.asyncio
    async def test_handle_invoice_received_event(self):
        """Test that invoice_received event creates parse task"""
        orchestrator = OrchestratorAgent()
        
        # Mock database
        db_mock = AsyncMock()
        
        # Create event
        event = AgentEvent(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            event_type="invoice_received",
            payload={"invoice_id": str(uuid.uuid4())},
            processed=False
        )
        
        # Handle event
        await orchestrator.handle_invoice_received(db_mock, event)
        
        # Verify task was added to database
        assert db_mock.add.called
        added_task = db_mock.add.call_args[0][0]
        assert isinstance(added_task, AgentTask)
        assert added_task.agent_type == "invoice_parser"
        assert added_task.task_type == "parse_invoice"
        
        # Verify commit was called
        assert db_mock.commit.called
    
    @pytest.mark.asyncio
    async def test_handle_invoice_parsed_event(self):
        """Test that invoice_parsed event creates booking task"""
        orchestrator = OrchestratorAgent()
        
        # Mock database
        db_mock = AsyncMock()
        
        invoice_id = uuid.uuid4()
        
        # Mock invoice lookup
        mock_invoice = VendorInvoice(
            id=invoice_id,
            client_id=uuid.uuid4(),
            invoice_number="TEST-001",
            invoice_date=date.today(),
            due_date=date.today(),
            amount_excl_vat=Decimal("1000.00"),
            vat_amount=Decimal("250.00"),
            total_amount=Decimal("1250.00")
        )
        
        db_mock.execute.return_value.scalar_one_or_none.return_value = mock_invoice
        
        # Create event
        event = AgentEvent(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            event_type="invoice_parsed",
            payload={"invoice_id": str(invoice_id)},
            processed=False
        )
        
        # Handle event
        await orchestrator.handle_invoice_parsed(db_mock, event)
        
        # Verify task was created
        assert db_mock.add.called
        added_task = db_mock.add.call_args[0][0]
        assert isinstance(added_task, AgentTask)
        assert added_task.agent_type == "bookkeeper"
        assert added_task.task_type == "book_invoice"
    
    @pytest.mark.asyncio
    async def test_evaluate_and_route_high_confidence(self):
        """Test auto-approve for high confidence booking"""
        orchestrator = OrchestratorAgent()
        
        # Mock database
        db_mock = AsyncMock()
        
        # Create journal entry with high confidence
        entry = GeneralLedger(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            entry_date=date.today(),
            accounting_date=date.today(),
            period="2024-02",
            fiscal_year=2024,
            voucher_number="1",
            description="Test entry",
            source_type="ehf_invoice",
            created_by_type="ai_agent",
            status="draft"
        )
        
        line = GeneralLedgerLine(
            id=uuid.uuid4(),
            general_ledger_id=entry.id,
            line_number=1,
            account_number="6300",
            debit_amount=Decimal("1000.00"),
            credit_amount=Decimal("0"),
            ai_confidence_score=92,  # High confidence
            ai_reasoning="Very confident about this booking"
        )
        
        entry.lines = [line]
        
        # Evaluate and route
        await orchestrator.evaluate_and_route(db_mock, entry)
        
        # Should auto-approve (confidence >= 85)
        assert db_mock.execute.called
        # Verify it tried to update status to 'posted'
        update_call = db_mock.execute.call_args[0][0]
        assert "posted" in str(update_call)
    
    @pytest.mark.asyncio
    async def test_evaluate_and_route_low_confidence(self):
        """Test review queue for low confidence booking"""
        orchestrator = OrchestratorAgent()
        
        # Mock database
        db_mock = AsyncMock()
        
        # Create journal entry with low confidence
        entry = GeneralLedger(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            entry_date=date.today(),
            accounting_date=date.today(),
            period="2024-02",
            fiscal_year=2024,
            voucher_number="1",
            description="Test entry",
            source_type="ehf_invoice",
            created_by_type="ai_agent",
            status="draft"
        )
        
        line = GeneralLedgerLine(
            id=uuid.uuid4(),
            general_ledger_id=entry.id,
            line_number=1,
            account_number="6300",
            debit_amount=Decimal("1000.00"),
            credit_amount=Decimal("0"),
            ai_confidence_score=45,  # Low confidence
            ai_reasoning="Not sure about this one"
        )
        
        entry.lines = [line]
        
        # Evaluate and route
        await orchestrator.evaluate_and_route(db_mock, entry)
        
        # Should send to review queue
        assert db_mock.add.called
        # Should have created a ReviewQueue item


class TestBookkeepingAgentMocked:
    """Test bookkeeping agent with mocks"""
    
    @pytest.mark.asyncio
    async def test_generate_fallback_booking(self):
        """Test fallback booking generation"""
        agent = BookkeepingAgent()
        
        # Create mock invoice
        invoice = VendorInvoice(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            invoice_number="TEST-001",
            invoice_date=date.today(),
            due_date=date.today(),
            amount_excl_vat=Decimal("1000.00"),
            vat_amount=Decimal("250.00"),
            total_amount=Decimal("1250.00")
        )
        
        # Generate fallback
        booking_data = agent._generate_fallback_booking(invoice)
        
        # Verify structure
        assert "lines" in booking_data
        assert "confidence_score" in booking_data
        assert "reasoning" in booking_data
        
        # Verify balance
        lines = booking_data["lines"]
        total_debit = sum(line["debit"] for line in lines)
        total_credit = sum(line["credit"] for line in lines)
        
        assert abs(total_debit - total_credit) < 0.01
        
        # Verify amounts
        assert total_credit == float(invoice.total_amount)
        
        # Verify low confidence
        assert booking_data["confidence_score"] <= 40


class TestInvoiceParserAgentMocked:
    """Test invoice parser agent with mocks"""
    
    @pytest.mark.asyncio
    async def test_find_or_create_vendor_new(self):
        """Test creating new vendor"""
        agent = InvoiceParserAgent()
        
        # Mock database
        db_mock = AsyncMock()
        db_mock.execute.return_value.scalar_one_or_none.return_value = None
        
        # Find or create
        vendor = await agent.find_or_create_vendor(
            db_mock,
            client_id=str(uuid.uuid4()),
            name="Test Vendor AS",
            org_number="123456789"
        )
        
        # Verify vendor was created
        assert db_mock.add.called
        assert db_mock.commit.called


class TestLearningAgentMocked:
    """Test learning agent with mocks"""
    
    def test_extract_keywords(self):
        """Test keyword extraction from correction reason"""
        agent = LearningAgent()
        
        # Test Norwegian text
        text = "PowerRent leverer møbler, ikke lokaler"
        keywords = agent._extract_keywords(text)
        
        # Should extract meaningful words
        assert "powerrent" in keywords or "møbler" in keywords or "lokaler" in keywords
        
        # Should not include stop words
        assert "ikke" not in keywords
        assert len(keywords) <= 5


# Integration tests (require database)
# These will be skipped if DATABASE_URL is not set

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_flow_integration(db_session):
    """
    Test complete flow from invoice to booking
    
    Requires:
    - Database with migrations run
    - Valid ANTHROPIC_API_KEY (or mock it)
    """
    # This is a placeholder for integration tests
    # Would need actual database setup
    pytest.skip("Integration test - requires database setup")


# Mock data helpers

def create_mock_ehf_invoice():
    """Create mock EHF invoice data"""
    return {
        "invoice_number": "TEST-001",
        "issue_date": date.today(),
        "due_date": date.today(),
        "supplier": {
            "name": "Test Supplier AS",
            "party_id": "123456789"
        },
        "tax_exclusive_amount": 1000.00,
        "tax_total": {
            "tax_amount": 250.00
        },
        "payable_amount": 1250.00,
        "document_currency_code": "NOK"
    }


def create_mock_booking_data():
    """Create mock booking data"""
    return {
        "lines": [
            {
                "account": "6300",
                "account_name": "Kontorkostnader",
                "debit": 1000.00,
                "credit": 0,
                "vat_code": "5",
                "description": "Office supplies"
            },
            {
                "account": "2740",
                "account_name": "Inngående MVA",
                "debit": 250.00,
                "credit": 0,
                "vat_code": None,
                "description": "VAT 25%"
            },
            {
                "account": "2400",
                "account_name": "Leverandørgjeld",
                "debit": 0,
                "credit": 1250.00,
                "vat_code": None,
                "description": "Accounts payable"
            }
        ],
        "confidence_score": 85,
        "reasoning": "Standard office supplies booking with VAT"
    }


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
