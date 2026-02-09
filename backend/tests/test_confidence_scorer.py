"""
Tests for Confidence Scoring Service
SkatteFUNN AP2: Tillitsmodell testing

Versjon: MVP 1.0
Dato: 2026-02-09
"""

import pytest
from decimal import Decimal
from app.services.confidence_scorer import ConfidenceScorer, score_invoice


@pytest.fixture
def scorer():
    """Fixture: ConfidenceScorer instance"""
    return ConfidenceScorer()


@pytest.fixture
def perfect_invoice():
    """Fixture: Perfect invoice with all fields"""
    return {
        'vendor_name': 'Acme Supplies AS',
        'invoice_number': 'INV-2026-001',
        'invoice_date': '2026-02-01',
        'due_date': '2026-02-28',
        'amount_ex_vat': 10000.00,
        'vat_amount': 2500.00,
        'total_amount': 12500.00,
        'vat_rate': 25,
        'suggested_account': '6420',
    }


@pytest.fixture
def incomplete_invoice():
    """Fixture: Invoice with missing fields"""
    return {
        'vendor_name': 'Test Vendor',
        'invoice_number': None,  # Missing
        'invoice_date': '2026-02-01',
        'due_date': None,  # Missing
        'amount_ex_vat': 5000.00,
        'vat_amount': 1250.00,
        'total_amount': 6250.00,
        'suggested_account': '6300',
    }


@pytest.fixture
def invalid_amounts_invoice():
    """Fixture: Invoice with mismatched amounts"""
    return {
        'vendor_name': 'Bad Math Corp',
        'invoice_number': 'INV-BAD-001',
        'invoice_date': '2026-02-01',
        'due_date': '2026-02-28',
        'amount_ex_vat': 10000.00,
        'vat_amount': 2500.00,
        'total_amount': 13000.00,  # WRONG! Should be 12500
        'suggested_account': '6420',
    }


class TestConfidenceScorer:
    """Test suite for ConfidenceScorer"""
    
    def test_perfect_invoice_high_score(self, scorer, perfect_invoice):
        """Perfect invoice with high OCR/AI confidence should score > 80%"""
        
        result = scorer.calculate_score(
            invoice_data=perfect_invoice,
            ocr_confidence=0.95,
            ai_confidence=0.90
        )
        
        assert result['total_score'] >= 0.80
        assert result['should_auto_approve'] is True
        assert result['recommendation'] == 'AUTO_APPROVE'
        assert 'breakdown' in result
        assert 'calculated_at' in result
    
    def test_low_ocr_confidence_escalates(self, scorer, perfect_invoice):
        """Low OCR confidence should trigger manual review"""
        
        result = scorer.calculate_score(
            invoice_data=perfect_invoice,
            ocr_confidence=0.40,  # Poor OCR quality
            ai_confidence=0.90
        )
        
        assert result['total_score'] < 0.80
        assert result['should_auto_approve'] is False
        assert result['recommendation'] == 'MANUAL_REVIEW'
    
    def test_low_ai_confidence_escalates(self, scorer, perfect_invoice):
        """Low AI confidence should trigger manual review"""
        
        result = scorer.calculate_score(
            invoice_data=perfect_invoice,
            ocr_confidence=0.95,
            ai_confidence=0.50  # AI uncertain about account
        )
        
        assert result['total_score'] < 0.80
        assert result['should_auto_approve'] is False
    
    def test_incomplete_invoice_lower_score(self, scorer, incomplete_invoice):
        """Missing required fields should reduce score"""
        
        result = scorer.calculate_score(
            invoice_data=incomplete_invoice,
            ocr_confidence=0.95,
            ai_confidence=0.90
        )
        
        # Field completeness is only 75% (6/8 fields)
        assert result['breakdown']['field_completeness'] < 1.0
        assert result['total_score'] < 0.90  # Should reduce overall score
    
    def test_invalid_amounts_low_validation_score(self, scorer, invalid_amounts_invoice):
        """Mismatched amounts should fail validation"""
        
        result = scorer.calculate_score(
            invoice_data=invalid_amounts_invoice,
            ocr_confidence=0.95,
            ai_confidence=0.90
        )
        
        # Amount validation should be low
        assert result['breakdown']['amount_validation'] < 0.5
        assert result['should_auto_approve'] is False
    
    def test_missing_ocr_confidence_defaults(self, scorer, perfect_invoice):
        """Missing OCR confidence should use default (0.5)"""
        
        result = scorer.calculate_score(
            invoice_data=perfect_invoice,
            ocr_confidence=None,  # Missing
            ai_confidence=0.90
        )
        
        assert result['breakdown']['ocr_quality'] == 0.5
    
    def test_missing_ai_confidence_defaults(self, scorer, perfect_invoice):
        """Missing AI confidence should use default (0.6)"""
        
        result = scorer.calculate_score(
            invoice_data=perfect_invoice,
            ocr_confidence=0.95,
            ai_confidence=None  # Missing
        )
        
        assert result['breakdown']['ai_confidence'] == 0.6
    
    def test_score_breakdown_weights_sum_to_one(self, scorer):
        """Weights should sum to 1.0 (100%)"""
        
        total_weight = sum(scorer.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01  # Allow tiny floating point error
    
    def test_vat_calculation_validation(self, scorer):
        """VAT calculation should validate correctly"""
        
        invoice = {
            'vendor_name': 'Test',
            'invoice_number': '001',
            'invoice_date': '2026-02-01',
            'due_date': '2026-02-28',
            'amount_ex_vat': 8000.00,
            'vat_amount': 2000.00,  # 25% of 8000
            'total_amount': 10000.00,
            'vat_rate': 25,
            'suggested_account': '6420',
        }
        
        result = scorer.calculate_score(invoice, 0.95, 0.90)
        assert result['breakdown']['amount_validation'] == 1.0
    
    def test_vat_calculation_mismatch(self, scorer):
        """Incorrect VAT calculation should reduce score"""
        
        invoice = {
            'vendor_name': 'Test',
            'invoice_number': '001',
            'invoice_date': '2026-02-01',
            'due_date': '2026-02-28',
            'amount_ex_vat': 8000.00,
            'vat_amount': 1500.00,  # WRONG! Should be 2000 (25% of 8000)
            'total_amount': 9500.00,
            'vat_rate': 25,
            'suggested_account': '6420',
        }
        
        result = scorer.calculate_score(invoice, 0.95, 0.90)
        assert result['breakdown']['amount_validation'] < 1.0
    
    def test_escalation_reason_generation(self, scorer, perfect_invoice):
        """Should generate human-readable escalation reason"""
        
        # Low OCR confidence
        result = scorer.calculate_score(perfect_invoice, 0.40, 0.90)
        reason = scorer.get_escalation_reason(result)
        assert 'OCR' in reason or 'text recognition' in reason
        
        # Low AI confidence
        result = scorer.calculate_score(perfect_invoice, 0.95, 0.40)
        reason = scorer.get_escalation_reason(result)
        assert 'AI' in reason or 'account suggestion' in reason
    
    def test_threshold_boundary_case(self, scorer, perfect_invoice):
        """Test exact threshold boundary (0.80)"""
        
        # Engineer a score exactly at threshold
        # This requires specific combination of factors
        # For now, just verify threshold is applied correctly
        
        result = scorer.calculate_score(perfect_invoice, 0.80, 0.80)
        
        if result['total_score'] >= 0.80:
            assert result['should_auto_approve'] is True
        else:
            assert result['should_auto_approve'] is False


class TestConvenienceFunction:
    """Test the async convenience function"""
    
    @pytest.mark.asyncio
    async def test_score_invoice_function(self, perfect_invoice):
        """Convenience function should work same as class method"""
        
        result = await score_invoice(
            invoice_data=perfect_invoice,
            ocr_confidence=0.95,
            ai_confidence=0.90
        )
        
        assert 'total_score' in result
        assert 'should_auto_approve' in result
        assert result['total_score'] >= 0.80


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_invoice_data(self, scorer):
        """Empty invoice data should not crash"""
        
        result = scorer.calculate_score({}, None, None)
        
        assert result['total_score'] >= 0.0
        assert result['total_score'] <= 1.0
        assert 'recommendation' in result
    
    def test_negative_amounts(self, scorer):
        """Negative amounts should be handled gracefully"""
        
        invoice = {
            'vendor_name': 'Test',
            'amount_ex_vat': -1000.00,
            'vat_amount': -250.00,
            'total_amount': -1250.00,
        }
        
        result = scorer.calculate_score(invoice, 0.95, 0.90)
        
        # Should not crash, score will be low
        assert result is not None
        assert 'total_score' in result
    
    def test_zero_amounts(self, scorer):
        """Zero amounts should be valid"""
        
        invoice = {
            'vendor_name': 'Free Sample Inc',
            'invoice_number': 'SAMPLE-001',
            'invoice_date': '2026-02-01',
            'due_date': '2026-02-28',
            'amount_ex_vat': 0.00,
            'vat_amount': 0.00,
            'total_amount': 0.00,
            'suggested_account': '6420',
        }
        
        result = scorer.calculate_score(invoice, 0.95, 0.90)
        
        # Should validate correctly (0 + 0 = 0)
        assert result['breakdown']['amount_validation'] == 1.0
    
    def test_very_large_amounts(self, scorer):
        """Very large amounts should work"""
        
        invoice = {
            'vendor_name': 'Big Corp',
            'invoice_number': 'MEGA-001',
            'invoice_date': '2026-02-01',
            'due_date': '2026-02-28',
            'amount_ex_vat': 10000000.00,  # 10 million
            'vat_amount': 2500000.00,
            'total_amount': 12500000.00,
            'vat_rate': 25,
            'suggested_account': '6420',
        }
        
        result = scorer.calculate_score(invoice, 0.95, 0.90)
        
        assert result['breakdown']['amount_validation'] == 1.0


# Run with: pytest tests/test_confidence_scorer.py -v --cov=app.services.confidence_scorer
