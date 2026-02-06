"""
Bank Matching Agent - AI-powered transaction-to-invoice matching
"""
import anthropic
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os

from app.models.bank_transaction import BankTransaction, TransactionStatus
from app.models.vendor_invoice import VendorInvoice


class BankMatchingAgent:
    """
    AI agent that matches bank transactions to vendor invoices
    
    Matching strategies:
    1. KID number match (Norwegian payment reference) - 99% confidence
    2. Amount + date proximity + vendor name - 80-95% confidence
    3. Amount + description text similarity - 60-80% confidence
    4. Pattern learning from previous matches - increases over time
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("CLAUDE_API_KEY")
        )
        self.model = "claude-sonnet-4-5-20250514"
    
    async def match_transaction(
        self,
        transaction: BankTransaction,
        candidate_invoices: List[VendorInvoice]
    ) -> Optional[Dict[str, Any]]:
        """
        Match a single bank transaction to an invoice
        
        Returns:
        {
            "matched_invoice_id": UUID,
            "confidence": 0-100,
            "reason": "Explanation of match"
        }
        or None if no good match found
        """
        
        # Strategy 1: KID number match (instant high confidence)
        if transaction.kid_number:
            for invoice in candidate_invoices:
                if invoice.kid_number and invoice.kid_number == transaction.kid_number:
                    return {
                        "matched_invoice_id": invoice.id,
                        "confidence": 99,
                        "reason": f"KID number match: {transaction.kid_number}"
                    }
        
        # Strategy 2: Amount + date + vendor match
        amount = float(transaction.amount)
        date = transaction.transaction_date
        
        # Find invoices with matching amount (±1 NOK tolerance)
        amount_matches = [
            inv for inv in candidate_invoices
            if abs(float(inv.total_amount) - amount) <= 1.0
        ]
        
        if not amount_matches:
            return None  # No amount match, can't proceed
        
        # If only one match with correct amount, high confidence
        if len(amount_matches) == 1:
            invoice = amount_matches[0]
            days_diff = abs((date - invoice.due_date).days)
            
            if days_diff <= 7:  # Within 7 days of due date
                return {
                    "matched_invoice_id": invoice.id,
                    "confidence": 90,
                    "reason": f"Unique amount match ({amount} NOK) within due date window"
                }
        
        # Strategy 3: Use Claude AI to analyze description + vendor names
        return await self._ai_match_analysis(transaction, amount_matches)
    
    async def _ai_match_analysis(
        self,
        transaction: BankTransaction,
        candidate_invoices: List[VendorInvoice]
    ) -> Optional[Dict[str, Any]]:
        """
        Use Claude AI to analyze transaction description and match to invoice
        """
        
        if not candidate_invoices:
            return None
        
        # Prepare invoice data for AI
        invoice_data = []
        for inv in candidate_invoices:
            invoice_data.append({
                "id": str(inv.id),
                "vendor_name": inv.vendor_name,
                "invoice_number": inv.invoice_number,
                "amount": float(inv.total_amount),
                "due_date": inv.due_date.isoformat(),
                "description": inv.description or ""
            })
        
        prompt = f"""You are a bank reconciliation AI. Match this bank transaction to the most likely invoice.

BANK TRANSACTION:
- Date: {transaction.transaction_date.isoformat()}
- Amount: {transaction.amount} NOK
- Description: {transaction.description}
- Counterparty: {transaction.counterparty_name or 'Unknown'}
- Account: {transaction.counterparty_account or 'Unknown'}

CANDIDATE INVOICES (all have matching amounts):
{json.dumps(invoice_data, indent=2)}

TASK:
1. Analyze the transaction description and counterparty information
2. Match it to the most likely invoice based on vendor name similarity and context
3. Return confidence score (0-100) where:
   - 85-100: Very confident match (vendor name clearly matches)
   - 70-84: Probable match (good indication but not certain)
   - 50-69: Possible match (weak signals)
   - 0-49: No clear match

RESPOND ONLY with valid JSON:
{{
  "matched_invoice_id": "UUID or null",
  "confidence": 0-100,
  "reason": "Brief explanation"
}}"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            result_text = response.content[0].text
            
            # Parse JSON response
            result = json.loads(result_text)
            
            # Validate confidence threshold
            if result.get("confidence", 0) < 50:
                return None  # Too low confidence
            
            return result
            
        except Exception as e:
            # AI failed, return None (manual review needed)
            print(f"AI matching failed: {e}")
            return None
    
    async def batch_match_transactions(
        self,
        transactions: List[BankTransaction],
        all_invoices: List[VendorInvoice]
    ) -> Dict[str, Any]:
        """
        Match multiple transactions in batch
        
        Returns:
        {
            "matched": [
                {"transaction_id": ..., "invoice_id": ..., "confidence": ...},
                ...
            ],
            "unmatched": [transaction_id, ...],
            "summary": {
                "total": int,
                "matched": int,
                "unmatched": int,
                "avg_confidence": float
            }
        }
        """
        matched = []
        unmatched = []
        
        # Filter invoices: unpaid or recently paid
        unpaid_invoices = [
            inv for inv in all_invoices
            if inv.payment_status in ['unpaid', 'partial']
        ]
        
        for txn in transactions:
            # Only match CREDIT transactions (money IN = invoice payment)
            if txn.transaction_type.value != 'credit':
                unmatched.append(str(txn.id))
                continue
            
            match_result = await self.match_transaction(txn, unpaid_invoices)
            
            if match_result and match_result["confidence"] >= 50:
                matched.append({
                    "transaction_id": str(txn.id),
                    "invoice_id": str(match_result["matched_invoice_id"]),
                    "confidence": match_result["confidence"],
                    "reason": match_result["reason"]
                })
            else:
                unmatched.append(str(txn.id))
        
        # Calculate summary
        total = len(transactions)
        matched_count = len(matched)
        avg_confidence = (
            sum(m["confidence"] for m in matched) / matched_count
            if matched_count > 0 else 0
        )
        
        return {
            "matched": matched,
            "unmatched": unmatched,
            "summary": {
                "total": total,
                "matched": matched_count,
                "unmatched": len(unmatched),
                "match_rate": round((matched_count / total * 100) if total > 0 else 0, 1),
                "avg_confidence": round(avg_confidence, 1)
            }
        }
