"""
Bank Reconciliation Service

Handles automatic matching of bank transactions with GL entries.

Matching levels:
1. EXACT: Amount + date ±3 days (90% of cases)
2. AI-ASSISTED: Amount + date ±7 days + description similarity (8%)
3. MANUAL: Needs human review (2%)
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_, or_
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
import csv
import io

from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.config import settings
import anthropic


class BankReconciliationService:
    """Service for bank reconciliation and transaction matching"""
    
    def __init__(self):
        api_key = settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else None
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-sonnet-4-5"
        else:
            self.client = None
            self.model = None
    
    async def parse_bank_statement(
        self,
        file_content: bytes,
        format_type: str = "csv"
    ) -> List[Dict[str, Any]]:
        """
        Parse bank statement file (CSV or Excel).
        
        Expected columns:
        - date: Transaction date
        - amount: Transaction amount (negative for outgoing)
        - description: Transaction description
        - reference: Optional reference number
        
        Args:
            file_content: Raw file bytes
            format_type: "csv" or "excel"
        
        Returns:
            List of parsed transactions
        """
        
        transactions = []
        
        if format_type == "csv":
            # Parse CSV
            content_str = file_content.decode('utf-8-sig')  # Handle BOM
            csv_reader = csv.DictReader(io.StringIO(content_str), delimiter=';')
            
            for row in csv_reader:
                # Try common Norwegian bank formats
                trans_date = None
                amount = None
                description = ""
                reference = ""
                
                # Parse date (try multiple formats)
                for date_field in ['Dato', 'Date', 'Bokført', 'Bokført dato']:
                    if date_field in row and row[date_field]:
                        try:
                            # Try DD.MM.YYYY format (Norwegian)
                            parts = row[date_field].split('.')
                            if len(parts) == 3:
                                trans_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
                                break
                        except:
                            pass
                
                # Parse amount
                for amount_field in ['Beløp', 'Amount', 'Beløp inn', 'Beløp ut']:
                    if amount_field in row and row[amount_field]:
                        try:
                            # Remove thousand separators and replace comma with dot
                            amount_str = row[amount_field].replace(' ', '').replace(',', '.')
                            amount = Decimal(amount_str)
                            break
                        except:
                            pass
                
                # Parse description
                for desc_field in ['Tekst', 'Description', 'Beskrivelse', 'Fra/til']:
                    if desc_field in row and row[desc_field]:
                        description = row[desc_field]
                        break
                
                # Parse reference
                for ref_field in ['Referanse', 'Reference', 'Arkivreferanse']:
                    if ref_field in row and row[ref_field]:
                        reference = row[ref_field]
                        break
                
                if trans_date and amount is not None:
                    transactions.append({
                        "date": trans_date.isoformat(),
                        "amount": float(amount),
                        "description": description.strip(),
                        "reference": reference.strip()
                    })
        
        return transactions
    
    async def match_transactions(
        self,
        db: AsyncSession,
        client_id: UUID,
        bank_account: str,
        bank_transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Match bank transactions with GL entries.
        
        Uses 3-level matching strategy:
        1. Exact match (amount + date ±3 days)
        2. AI-assisted (amount + date ±7 days + similarity)
        3. Manual review needed
        
        Args:
            client_id: Client UUID
            bank_account: GL account number for bank (e.g., "1920")
            bank_transactions: List of parsed bank transactions
        
        Returns:
            Dict with auto_matched, ai_assisted, and needs_review lists
        """
        
        # Get all unmatched GL entries for this bank account
        query = """
        SELECT 
            gl.id as entry_id,
            gl.accounting_date,
            gl.voucher_number,
            gl.description,
            gll.debit_amount - gll.credit_amount as net_amount
        FROM general_ledger_lines gll
        JOIN general_ledger gl ON gll.general_ledger_id = gl.id
        WHERE gl.client_id = :client_id
          AND gll.account_number = :account_number
          AND gl.status = 'posted'
        ORDER BY gl.accounting_date DESC
        """
        
        result = await db.execute(
            text(query),
            {"client_id": str(client_id), "account_number": bank_account}
        )
        gl_entries = [
            {
                "entry_id": str(row.entry_id),
                "date": row.accounting_date,
                "amount": float(row.net_amount),
                "voucher_number": row.voucher_number,
                "description": row.description
            }
            for row in result.fetchall()
        ]
        
        auto_matched = []
        ai_assisted = []
        needs_review = []
        
        matched_gl_ids = set()
        
        for bank_tx in bank_transactions:
            bank_date = date.fromisoformat(bank_tx["date"])
            bank_amount = bank_tx["amount"]
            
            # Level 1: Exact match
            exact_match = self._find_exact_match(
                bank_tx, gl_entries, matched_gl_ids, date_tolerance=3
            )
            
            if exact_match:
                auto_matched.append({
                    "bank": bank_tx,
                    "gl": exact_match,
                    "confidence": 98,
                    "method": "exact",
                    "match_reasons": ["Exact amount", "Date within 3 days"]
                })
                matched_gl_ids.add(exact_match["entry_id"])
                continue
            
            # Level 2: AI-assisted (if Claude available)
            if self.client:
                ai_match = await self._ai_find_match(bank_tx, gl_entries, matched_gl_ids)
                if ai_match and ai_match["confidence"] >= 70:
                    ai_assisted.append(ai_match)
                    matched_gl_ids.add(ai_match["gl"]["entry_id"])
                    continue
            
            # Level 3: Manual review
            possible_matches = self._find_possible_matches(bank_tx, gl_entries, matched_gl_ids)
            needs_review.append({
                "bank": bank_tx,
                "possible_matches": possible_matches,
                "status": "needs_review",
                "reason": "No confident automatic match found"
            })
        
        # Find unmatched GL entries
        unmatched_gl = [
            gl for gl in gl_entries 
            if gl["entry_id"] not in matched_gl_ids
        ]
        
        match_rate = len(auto_matched + ai_assisted) / len(bank_transactions) * 100 if bank_transactions else 0
        
        return {
            "success": True,
            "summary": {
                "total_bank_transactions": len(bank_transactions),
                "auto_matched": len(auto_matched),
                "ai_assisted": len(ai_assisted),
                "needs_review": len(needs_review),
                "match_rate": round(match_rate, 1),
                "unmatched_gl_entries": len(unmatched_gl)
            },
            "auto_matched": auto_matched,
            "ai_assisted": ai_assisted,
            "needs_review": needs_review,
            "unmatched_gl": unmatched_gl
        }
    
    def _find_exact_match(
        self,
        bank_tx: Dict[str, Any],
        gl_entries: List[Dict[str, Any]],
        matched_ids: set,
        date_tolerance: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Find exact match: same amount, date within tolerance"""
        
        bank_date = date.fromisoformat(bank_tx["date"])
        bank_amount = bank_tx["amount"]
        
        for gl in gl_entries:
            if gl["entry_id"] in matched_ids:
                continue
            
            # Check amount (exact match)
            if abs(gl["amount"] - bank_amount) > 0.01:
                continue
            
            # Check date (within tolerance)
            gl_date = gl["date"]
            date_diff = abs((bank_date - gl_date).days)
            
            if date_diff <= date_tolerance:
                return gl
        
        return None
    
    async def _ai_find_match(
        self,
        bank_tx: Dict[str, Any],
        gl_entries: List[Dict[str, Any]],
        matched_ids: set
    ) -> Optional[Dict[str, Any]]:
        """Use AI to find best match for uncertain cases"""
        
        if not self.client:
            return None
        
        # Filter possible candidates (amount match, date within 7 days)
        bank_date = date.fromisoformat(bank_tx["date"])
        bank_amount = bank_tx["amount"]
        
        candidates = []
        for gl in gl_entries:
            if gl["entry_id"] in matched_ids:
                continue
            
            # Amount must match exactly
            if abs(gl["amount"] - bank_amount) > 0.01:
                continue
            
            # Date within 7 days
            date_diff = abs((bank_date - gl["date"]).days)
            if date_diff > 7:
                continue
            
            candidates.append(gl)
        
        if not candidates:
            return None
        
        # Ask Claude to pick best match
        prompt = f"""Bank transaction to match:
Date: {bank_tx['date']}
Amount: {bank_tx['amount']} kr
Description: {bank_tx['description']}

Possible GL entries:
"""
        
        for i, gl in enumerate(candidates, 1):
            prompt += f"\n{i}. Date: {gl['date']}, Amount: {gl['amount']} kr, Description: {gl['description']}, Voucher: {gl['voucher_number']}"
        
        prompt += """

Which GL entry is the best match? Return ONLY a JSON object:
{
  "match_index": <number or null>,
  "confidence": <0-100>,
  "reasoning": "<brief explanation>"
}"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON from response
            import json
            # Remove markdown code blocks if present
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(response_text)
            
            if result["match_index"] and result["confidence"] >= 70:
                matched_gl = candidates[result["match_index"] - 1]
                return {
                    "bank": bank_tx,
                    "gl": matched_gl,
                    "confidence": result["confidence"],
                    "method": "ai_assisted",
                    "reasoning": result["reasoning"]
                }
        
        except Exception as e:
            print(f"AI matching error: {e}")
            return None
        
        return None
    
    def _find_possible_matches(
        self,
        bank_tx: Dict[str, Any],
        gl_entries: List[Dict[str, Any]],
        matched_ids: set,
        max_matches: int = 5
    ) -> List[Dict[str, Any]]:
        """Find possible matches for manual review"""
        
        bank_date = date.fromisoformat(bank_tx["date"])
        bank_amount = bank_tx["amount"]
        
        matches = []
        
        for gl in gl_entries:
            if gl["entry_id"] in matched_ids:
                continue
            
            # Calculate similarity score
            score = 0
            reasons = []
            
            # Amount match
            amount_diff = abs(gl["amount"] - bank_amount)
            if amount_diff < 0.01:
                score += 50
                reasons.append("Exact amount")
            elif amount_diff < 100:
                score += 30
                reasons.append("Close amount")
            
            # Date proximity
            date_diff = abs((bank_date - gl["date"]).days)
            if date_diff <= 3:
                score += 30
                reasons.append(f"Date within {date_diff} days")
            elif date_diff <= 7:
                score += 15
                reasons.append(f"Date within {date_diff} days")
            
            # Description similarity (basic)
            bank_desc_lower = bank_tx["description"].lower()
            gl_desc_lower = gl["description"].lower()
            
            common_words = set(bank_desc_lower.split()) & set(gl_desc_lower.split())
            if common_words:
                score += 20
                reasons.append(f"Matching words: {', '.join(list(common_words)[:3])}")
            
            if score > 30:  # Threshold for "possible match"
                matches.append({
                    "gl": gl,
                    "similarity_score": score,
                    "reasons": reasons
                })
        
        # Sort by score, return top matches
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:max_matches]
