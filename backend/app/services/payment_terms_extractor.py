"""
Payment Terms Extraction Service

Features:
1. Parse payment terms from Norwegian text
2. Common formats:
   - "30 dager netto"
   - "Netto 14 dager"
   - "Betales ved mottak" (immediate)
   - "Forfaller [date]"
3. Store as payment_terms_days in vendor_invoice
4. Auto-calculate due_date if missing from OCR
5. Use regex for simple cases, GPT for complex cases

Note: OCR already extracts due_date, this enhances it.
"""
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, date
import re
import uuid
from anthropic import AsyncAnthropic

from app.models import VendorInvoice
from app.config import settings


class PaymentTermsExtractor:
    """
    Payment Terms Extraction Service
    
    Extracts and normalizes payment terms from invoice text
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize Anthropic client if available
        self.anthropic_client = None
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Common Norwegian payment terms patterns
        self.patterns = [
            # "30 dager netto" / "netto 30 dager"
            (r'(?:netto\s*)?(\d+)\s*dager?(?:\s*netto)?', 'days'),
            
            # "Forfaller dd.mm.yyyy" / "Forfall: dd.mm.yyyy"
            (r'forf[ao]ller?:?\s*(\d{1,2})[./\-](\d{1,2})[./\-](\d{2,4})', 'due_date'),
            
            # "Betales ved mottak" / "Ved mottak" (immediate)
            (r'(?:betales\s*)?ved\s*mottak', 'immediate'),
            
            # "Kontant" / "Kontantbetaling"
            (r'kontant(?:betaling)?', 'immediate'),
            
            # "8 dagers netto"
            (r'(\d+)\s*dagers?\s*netto', 'days'),
            
            # "Betalingsfrist: X dager"
            (r'betalings?frist:?\s*(\d+)\s*dager?', 'days'),
            
            # "Forfallsdato: dd.mm.yyyy"
            (r'forfallsdato:?\s*(\d{1,2})[./\-](\d{1,2})[./\-](\d{2,4})', 'due_date'),
            
            # Standard terms like "Net 30", "NET 14"
            (r'net\s*(\d+)', 'days'),
        ]
    
    def extract_payment_terms(
        self,
        text: str,
        invoice_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Extract payment terms from text
        
        Returns:
        {
            "payment_days": int or None,
            "due_date": date or None,
            "terms_text": str (original text found),
            "confidence": int (0-100)
        }
        """
        if not text:
            return {
                "payment_days": None,
                "due_date": None,
                "terms_text": None,
                "confidence": 0
            }
        
        text_lower = text.lower()
        
        # Try each pattern
        for pattern, pattern_type in self.patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                result = self._parse_match(match, pattern_type, invoice_date)
                if result:
                    return result
        
        # No pattern matched
        return {
            "payment_days": None,
            "due_date": None,
            "terms_text": None,
            "confidence": 0
        }
    
    def _parse_match(
        self,
        match: re.Match,
        pattern_type: str,
        invoice_date: Optional[date]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse regex match into structured payment terms
        """
        if pattern_type == 'days':
            # Extract number of days
            days = int(match.group(1))
            
            # Calculate due date if invoice_date available
            due_date = None
            if invoice_date:
                due_date = invoice_date + timedelta(days=days)
            
            return {
                "payment_days": days,
                "due_date": due_date,
                "terms_text": match.group(0),
                "confidence": 90
            }
        
        elif pattern_type == 'immediate':
            # Immediate payment (0 days)
            due_date = None
            if invoice_date:
                due_date = invoice_date
            
            return {
                "payment_days": 0,
                "due_date": due_date,
                "terms_text": match.group(0),
                "confidence": 85
            }
        
        elif pattern_type == 'due_date':
            # Extract explicit due date
            try:
                day = int(match.group(1))
                month = int(match.group(2))
                year_str = match.group(3)
                
                # Handle 2-digit year
                year = int(year_str)
                if year < 100:
                    year += 2000
                
                due_date = date(year, month, day)
                
                # Calculate payment days if invoice_date available
                payment_days = None
                if invoice_date and due_date > invoice_date:
                    payment_days = (due_date - invoice_date).days
                
                return {
                    "payment_days": payment_days,
                    "due_date": due_date,
                    "terms_text": match.group(0),
                    "confidence": 95
                }
            except (ValueError, IndexError):
                # Invalid date
                return None
        
        return None
    
    async def extract_with_ai(
        self,
        text: str,
        invoice_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Use Claude AI to extract complex payment terms
        
        Fallback for cases where regex doesn't work
        """
        if not self.anthropic_client:
            return {
                "payment_days": None,
                "due_date": None,
                "terms_text": None,
                "confidence": 0,
                "error": "AI client not configured"
            }
        
        invoice_date_str = invoice_date.isoformat() if invoice_date else "unknown"
        
        prompt = f"""Extract payment terms from this Norwegian invoice text.

Invoice text:
{text[:1000]}  # Limit to first 1000 chars

Invoice date: {invoice_date_str}

Find payment terms like:
- "30 dager netto"
- "Betales ved mottak"
- "Forfaller dd.mm.yyyy"

Respond in JSON format:
{{
  "payment_days": <number of days or null>,
  "due_date": "<YYYY-MM-DD or null>",
  "terms_text": "<exact text found>",
  "confidence": <0-100>
}}

If no payment terms found, return all null/0."""
        
        try:
            message = await self.anthropic_client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=500,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            response_text = message.content[0].text.strip()
            
            # Extract JSON from response
            import json
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Convert due_date string to date object
                if result.get('due_date'):
                    try:
                        result['due_date'] = datetime.fromisoformat(result['due_date']).date()
                    except (ValueError, TypeError):
                        result['due_date'] = None
                
                return result
            
            return {
                "payment_days": None,
                "due_date": None,
                "terms_text": None,
                "confidence": 0,
                "error": "Could not parse AI response"
            }
            
        except Exception as e:
            return {
                "payment_days": None,
                "due_date": None,
                "terms_text": None,
                "confidence": 0,
                "error": str(e)
            }
    
    async def update_invoice_payment_terms(
        self,
        invoice_id: uuid.UUID,
        ocr_text: Optional[str] = None,
        use_ai_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Extract and update payment terms for an invoice
        
        Steps:
        1. Try regex extraction
        2. If confidence < 70 and use_ai_fallback, try AI
        3. Update invoice.payment_terms_days
        4. Auto-calculate due_date if missing
        
        Returns extraction result
        """
        # Get invoice
        result = await self.db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return {"error": "Invoice not found"}
        
        # Build text to analyze
        text_parts = []
        if ocr_text:
            text_parts.append(ocr_text)
        if hasattr(invoice, 'description') and invoice.description:
            text_parts.append(invoice.description)
        
        full_text = "\n".join(text_parts)
        
        if not full_text:
            return {"error": "No text to analyze"}
        
        # Try regex extraction first
        result = self.extract_payment_terms(full_text, invoice.invoice_date)
        
        # If low confidence and AI available, try AI
        if result['confidence'] < 70 and use_ai_fallback and self.anthropic_client:
            ai_result = await self.extract_with_ai(full_text, invoice.invoice_date)
            if ai_result.get('confidence', 0) > result['confidence']:
                result = ai_result
        
        # Update invoice if we found something
        if result.get('payment_days') is not None:
            # Store payment_days (we'll need to add this field via migration)
            if hasattr(invoice, 'payment_terms_days'):
                invoice.payment_terms_days = result['payment_days']
            
            # Update due_date if not set or if our calculation is different
            if result.get('due_date'):
                if not invoice.due_date or invoice.due_date != result['due_date']:
                    invoice.due_date = result['due_date']
            elif result['payment_days'] and invoice.invoice_date:
                # Calculate due_date from payment_days
                calculated_due = invoice.invoice_date + timedelta(days=result['payment_days'])
                if not invoice.due_date or invoice.due_date != calculated_due:
                    invoice.due_date = calculated_due
            
            invoice.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(invoice)
        
        return result
    
    def normalize_payment_terms_text(self, payment_days: int) -> str:
        """
        Convert payment_days to standard Norwegian text
        
        Examples:
        - 0 → "Betales ved mottak"
        - 14 → "14 dager netto"
        - 30 → "30 dager netto"
        """
        if payment_days == 0:
            return "Betales ved mottak"
        elif payment_days == 1:
            return "1 dag netto"
        else:
            return f"{payment_days} dager netto"
    
    async def bulk_update_payment_terms(
        self,
        client_id: uuid.UUID,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk update payment terms for invoices without them
        
        Processes invoices that don't have payment_terms_days set
        Returns summary of updates
        """
        # Get invoices without payment terms
        query = select(VendorInvoice).where(
            and_(
                VendorInvoice.client_id == client_id,
                # Only if we add payment_terms_days field
                # VendorInvoice.payment_terms_days.is_(None)
            )
        ).limit(limit)
        
        result = await self.db.execute(query)
        invoices = result.scalars().all()
        
        updated_count = 0
        failed_count = 0
        
        for invoice in invoices:
            try:
                result = await self.update_invoice_payment_terms(invoice.id)
                if result.get('payment_days') is not None:
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
        
        return {
            "total_processed": len(invoices),
            "updated": updated_count,
            "failed": failed_count
        }


# Helper functions
async def extract_invoice_payment_terms(
    db: AsyncSession,
    invoice_id: uuid.UUID,
    ocr_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to extract payment terms
    """
    service = PaymentTermsExtractor(db)
    return await service.update_invoice_payment_terms(invoice_id, ocr_text)


async def calculate_due_date(
    invoice_date: date,
    payment_terms_text: str
) -> Optional[date]:
    """
    Calculate due date from payment terms text
    """
    extractor = PaymentTermsExtractor(None)
    result = extractor.extract_payment_terms(payment_terms_text, invoice_date)
    return result.get('due_date')
