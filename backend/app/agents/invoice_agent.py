"""
Invoice Agent - AI for analyzing and booking invoices
"""
import anthropic
import json
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class InvoiceAgent:
    """
    Invoice Agent - Analyzes invoices and suggests bookings
    
    Uses Claude API to:
    - Extract structured data from OCR text
    - Match vendors
    - Suggest chart of accounts
    - Calculate confidence scores
    - Learn from vendor history and patterns
    """
    
    def __init__(self):
        """Initialize Claude client"""
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set - Invoice Agent will not work")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
    
    async def analyze_invoice(
        self,
        ocr_text: str,
        client_id: str,
        vendor_history: Optional[Dict] = None,
        learned_patterns: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Analyze invoice and suggest booking
        
        Args:
            ocr_text: Extracted text from PDF (via AWS Textract)
            client_id: Client UUID
            vendor_history: Previous invoices from same vendor
            learned_patterns: Learned patterns that might apply
        
        Returns:
            {
                'vendor': {'name': '...', 'org_number': '...'},
                'invoice_number': '...',
                'invoice_date': '...',
                'due_date': '...',
                'amount_excl_vat': 1000.00,
                'vat_amount': 250.00,
                'total_amount': 1250.00,
                'currency': 'NOK',
                'line_items': [...],
                'suggested_booking': [
                    {'account': '6300', 'debit': 1000, 'description': '...'},
                    {'account': '2740', 'debit': 250, 'description': 'VAT'},
                    {'account': '2400', 'credit': 1250, 'description': 'Payable'}
                ],
                'confidence_score': 92,
                'reasoning': 'This invoice is from a known vendor...'
            }
        """
        
        if not self.client:
            raise Exception("Claude API not configured. Set ANTHROPIC_API_KEY in environment.")
        
        # Build context with history and patterns
        context = self._build_context(vendor_history, learned_patterns)
        
        # Construct prompt for Claude
        prompt = self._build_prompt(ocr_text, context)
        
        try:
            # Call Claude API
            logger.info(f"Analyzing invoice for client {client_id}")
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            response_text = message.content[0].text
            result = json.loads(response_text)
            
            # Adjust confidence based on patterns
            if learned_patterns:
                result['confidence_score'] = self._adjust_confidence(
                    result,
                    learned_patterns
                )
            
            logger.info(
                f"Invoice analyzed successfully. Confidence: {result.get('confidence_score')}%"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            return {
                'error': 'Failed to parse invoice',
                'confidence_score': 0,
                'reasoning': 'Could not extract structured data from invoice'
            }
        
        except Exception as e:
            logger.error(f"Error analyzing invoice: {str(e)}")
            raise
    
    def _build_context(
        self,
        vendor_history: Optional[Dict],
        learned_patterns: Optional[List[Dict]]
    ) -> str:
        """Build context string from history and patterns"""
        context = ""
        
        if vendor_history:
            context += f"""
Previous invoices from this vendor:
{json.dumps(vendor_history, indent=2)}

Use the previous booking pattern as guidance.
"""
        
        if learned_patterns:
            context += f"""
Learned patterns that might apply:
{json.dumps(learned_patterns, indent=2)}

If a pattern matches, apply it and increase confidence.
"""
        
        return context
    
    def _build_prompt(self, ocr_text: str, context: str) -> str:
        """Build Claude prompt"""
        return f"""You are an expert Norwegian accountant analyzing an invoice.

OCR Text from Invoice:
{ocr_text}

{context}

Please analyze this invoice and provide a JSON response with the following structure:
{{
    "vendor": {{
        "name": "Vendor name",
        "org_number": "Organization number if found (9 digits)"
    }},
    "invoice_number": "Invoice number",
    "invoice_date": "YYYY-MM-DD",
    "due_date": "YYYY-MM-DD",
    "amount_excl_vat": 0.00,
    "vat_amount": 0.00,
    "total_amount": 0.00,
    "currency": "NOK",
    "line_items": [
        {{"description": "...", "amount": 0.00, "vat_code": "5"}}
    ],
    "suggested_booking": [
        {{"account": "6300", "debit": 1000, "credit": 0, "description": "Office supplies"}},
        {{"account": "2740", "debit": 250, "credit": 0, "description": "Input VAT 25%"}},
        {{"account": "2400", "debit": 0, "credit": 1250, "description": "Accounts payable"}}
    ],
    "confidence_score": 0-100,
    "reasoning": "Brief explanation of your analysis and booking suggestion"
}}

Important rules:
1. Use Norwegian chart of accounts (NS 4102)
2. Common expense accounts:
   - 6000-6099: Inventory/materials
   - 6100-6199: Services
   - 6300-6399: Office expenses
   - 6500-6599: Travel
   - 6700-6799: Marketing
3. VAT accounts:
   - 2740: Input VAT (deductible)
   - 2700: Output VAT
4. Payables: 2400-2499
5. Ensure debit = credit (balanced entry)
6. VAT code: 5 = 25%, 3 = 15%, 0 = exempt

Only return the JSON object, no other text."""
    
    def _adjust_confidence(
        self,
        result: Dict,
        patterns: List[Dict]
    ) -> int:
        """Adjust confidence based on learned patterns"""
        base_confidence = result.get('confidence_score', 50)
        
        # Boost confidence if matches high-success pattern
        for pattern in patterns:
            if pattern.get('success_rate', 0) > 0.90:
                base_confidence = min(100, base_confidence + 15)
                logger.info(f"Confidence boosted by pattern: {pattern.get('pattern_name')}")
                break
        
        return base_confidence
