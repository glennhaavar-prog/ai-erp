"""
AI Categorization Service - Smart Expense Categorization

Suggests accounting accounts based on:
- Historical vendor → account patterns
- Invoice description keywords
- Learned patterns from past bookings

Integrates with Review Queue to display suggestions with confidence scores.
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import uuid
import json
import re
from decimal import Decimal

from app.models import (
    VendorInvoice,
    Vendor,
    GeneralLedger,
    GeneralLedgerLine,
    AgentLearnedPattern
)


class AICategorization:
    """Represents a categorization suggestion"""
    def __init__(
        self,
        account_number: str,
        confidence: int,
        reason: str,
        keywords_matched: List[str] = None,
        historical_count: int = 0
    ):
        self.account_number = account_number
        self.confidence = confidence  # 0-100
        self.reason = reason
        self.keywords_matched = keywords_matched or []
        self.historical_count = historical_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_number": self.account_number,
            "confidence": self.confidence,
            "reason": self.reason,
            "keywords_matched": self.keywords_matched,
            "historical_count": self.historical_count
        }


class AICategorizationService:
    """
    Smart Expense Categorization Service
    
    Features:
    1. Learn from historical bookings (vendor → account patterns)
    2. Extract keywords from descriptions
    3. Store patterns in agent_learned_patterns table
    4. Suggest accounts with confidence scores
    5. Auto-improve from corrections
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Common Norwegian expense keywords → account mappings
        self.keyword_patterns = {
            "4000": ["kontorrekvisita", "papir", "perm", "blyant", "kontor"],
            "4100": ["lønn", "salary", "payroll"],
            "5000": ["konsulent", "rådgiver", "consultant"],
            "6000": ["leie", "rent", "husleie"],
            "6100": ["strøm", "elektrisitet", "power", "electricity"],
            "6300": ["forsikring", "insurance"],
            "6340": ["telefon", "mobil", "telenor", "telia"],
            "6540": ["annonsering", "markedsføring", "marketing", "ads"],
            "6700": ["reise", "hotell", "fly", "travel", "hotel"],
            "6900": ["representasjon", "møte", "catering"],
            "7140": ["programvare", "software", "lisens", "subscription", "saas"],
        }
    
    async def suggest_account(
        self,
        vendor_invoice: VendorInvoice,
        vendor: Optional[Vendor] = None
    ) -> List[AICategorization]:
        """
        Suggest accounting account(s) for a vendor invoice
        
        Returns list of suggestions sorted by confidence (highest first)
        """
        suggestions = []
        
        # Get vendor if not provided
        if not vendor and vendor_invoice.vendor_id:
            result = await self.db.execute(
                select(Vendor).where(Vendor.id == vendor_invoice.vendor_id)
            )
            vendor = result.scalar_one_or_none()
        
        # 1. Check historical patterns (highest confidence)
        if vendor:
            historical_suggestions = await self._get_historical_patterns(vendor)
            suggestions.extend(historical_suggestions)
        
        # 2. Analyze invoice description with keywords
        if hasattr(vendor_invoice, 'description') and vendor_invoice.description:
            keyword_suggestions = await self._analyze_description(
                vendor_invoice.description,
                vendor_invoice.client_id
            )
            suggestions.extend(keyword_suggestions)
        
        # 3. Check learned patterns from AI agent
        learned_suggestions = await self._get_learned_patterns(
            vendor_invoice.vendor_id,
            vendor_invoice.client_id
        )
        suggestions.extend(learned_suggestions)
        
        # Merge and rank suggestions
        merged = self._merge_suggestions(suggestions)
        
        # Sort by confidence (highest first)
        merged.sort(key=lambda x: x.confidence, reverse=True)
        
        return merged[:3]  # Return top 3
    
    async def _get_historical_patterns(
        self,
        vendor: Vendor
    ) -> List[AICategorization]:
        """
        Get account suggestions based on historical bookings for this vendor
        
        Analyzes past invoices and their booked accounts
        """
        suggestions = []
        
        # Find past booked invoices from this vendor
        query = select(
            GeneralLedgerLine.account_number,
            func.count().label('count')
        ).join(
            GeneralLedger,
            GeneralLedger.id == GeneralLedgerLine.general_ledger_id
        ).join(
            VendorInvoice,
            VendorInvoice.general_ledger_id == GeneralLedger.id
        ).where(
            and_(
                VendorInvoice.vendor_id == vendor.id,
                VendorInvoice.general_ledger_id.isnot(None),
                GeneralLedgerLine.account_number.like('4%')  # Expense accounts
            )
        ).group_by(
            GeneralLedgerLine.account_number
        ).order_by(
            desc('count')
        ).limit(3)
        
        result = await self.db.execute(query)
        patterns = result.all()
        
        total_count = sum(p.count for p in patterns)
        
        for pattern in patterns:
            if total_count > 0:
                # Confidence based on frequency
                frequency = pattern.count / total_count
                confidence = min(95, int(frequency * 100) + 50)  # 50-95%
                
                suggestions.append(AICategorization(
                    account_number=pattern.account_number,
                    confidence=confidence,
                    reason=f"Vendor historically uses this account ({pattern.count} times)",
                    historical_count=pattern.count
                ))
        
        return suggestions
    
    async def _analyze_description(
        self,
        description: str,
        client_id: uuid.UUID
    ) -> List[AICategorization]:
        """
        Analyze invoice description for keywords
        
        Uses predefined patterns + learned patterns
        """
        suggestions = []
        description_lower = description.lower()
        
        # Check each keyword pattern
        for account, keywords in self.keyword_patterns.items():
            matched_keywords = []
            for keyword in keywords:
                if keyword in description_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # Confidence based on number of keyword matches
                confidence = min(85, 60 + len(matched_keywords) * 10)
                
                suggestions.append(AICategorization(
                    account_number=account,
                    confidence=confidence,
                    reason=f"Matched keywords: {', '.join(matched_keywords)}",
                    keywords_matched=matched_keywords
                ))
        
        return suggestions
    
    async def _get_learned_patterns(
        self,
        vendor_id: Optional[uuid.UUID],
        client_id: uuid.UUID
    ) -> List[AICategorization]:
        """
        Get suggestions from AI-learned patterns
        
        Uses agent_learned_patterns table
        """
        suggestions = []
        
        query = select(AgentLearnedPattern).where(
            and_(
                AgentLearnedPattern.client_id == client_id,
                AgentLearnedPattern.pattern_type == 'vendor_categorization',
                AgentLearnedPattern.confidence >= 70
            )
        )
        
        if vendor_id:
            query = query.where(
                AgentLearnedPattern.pattern_data['vendor_id'].astext == str(vendor_id)
            )
        
        result = await self.db.execute(query.order_by(desc(AgentLearnedPattern.confidence)).limit(5))
        patterns = result.scalars().all()
        
        for pattern in patterns:
            if pattern.pattern_data and 'account_number' in pattern.pattern_data:
                suggestions.append(AICategorization(
                    account_number=pattern.pattern_data['account_number'],
                    confidence=pattern.confidence,
                    reason=pattern.reasoning or "AI learned pattern"
                ))
        
        return suggestions
    
    def _merge_suggestions(
        self,
        suggestions: List[AICategorization]
    ) -> List[AICategorization]:
        """
        Merge duplicate suggestions and boost confidence
        
        If multiple sources suggest same account, increase confidence
        """
        merged_dict = {}
        
        for suggestion in suggestions:
            account = suggestion.account_number
            
            if account in merged_dict:
                # Boost confidence (but cap at 99)
                existing = merged_dict[account]
                existing.confidence = min(99, existing.confidence + 10)
                
                # Combine reasons
                if suggestion.reason not in existing.reason:
                    existing.reason += f"; {suggestion.reason}"
                
                # Combine keywords
                existing.keywords_matched.extend(suggestion.keywords_matched)
                existing.keywords_matched = list(set(existing.keywords_matched))
                
                # Add historical count
                existing.historical_count += suggestion.historical_count
            else:
                merged_dict[account] = suggestion
        
        return list(merged_dict.values())
    
    async def learn_from_booking(
        self,
        vendor_invoice: VendorInvoice,
        booked_account: str
    ) -> None:
        """
        Learn from a confirmed booking
        
        Stores pattern in agent_learned_patterns for future suggestions
        """
        if not vendor_invoice.vendor_id:
            return
        
        # Get vendor
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_invoice.vendor_id)
        )
        vendor = result.scalar_one_or_none()
        
        if not vendor:
            return
        
        # Extract keywords from description
        keywords = []
        if hasattr(vendor_invoice, 'description') and vendor_invoice.description:
            # Simple keyword extraction (words > 4 chars)
            words = re.findall(r'\b\w{4,}\b', vendor_invoice.description.lower())
            keywords = list(set(words))[:10]  # Max 10 keywords
        
        # Store learned pattern
        pattern_data = {
            "vendor_id": str(vendor_invoice.vendor_id),
            "vendor_name": vendor.name,
            "account_number": booked_account,
            "keywords": keywords,
            "amount": float(vendor_invoice.total_amount)
        }
        
        # Use upsert to update existing pattern or create new
        stmt = insert(AgentLearnedPattern).values(
            id=uuid.uuid4(),
            client_id=vendor_invoice.client_id,
            pattern_type="vendor_categorization",
            pattern_data=pattern_data,
            confidence=75,  # Initial confidence
            sample_size=1,
            accuracy_rate=Decimal("1.0"),
            last_seen_at=datetime.utcnow(),
            reasoning=f"Learned from booking: {vendor.name} → Account {booked_account}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ).on_conflict_do_update(
            index_elements=['client_id', 'pattern_type'],
            where=and_(
                AgentLearnedPattern.pattern_data['vendor_id'].astext == str(vendor_invoice.vendor_id),
                AgentLearnedPattern.pattern_data['account_number'].astext == booked_account
            ),
            set_={
                'sample_size': AgentLearnedPattern.sample_size + 1,
                'confidence': func.least(95, AgentLearnedPattern.confidence + 2),
                'last_seen_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        )
        
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def update_invoice_suggestion(
        self,
        invoice_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Update vendor invoice with AI categorization suggestion
        
        Called when invoice is created or updated
        Returns the suggestion dict that was stored
        """
        # Get invoice
        result = await self.db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return None
        
        # Get suggestions
        suggestions = await self.suggest_account(invoice)
        
        if not suggestions:
            return None
        
        # Store top suggestion in invoice
        top_suggestion = suggestions[0]
        
        suggestion_dict = {
            "account_number": top_suggestion.account_number,
            "confidence": top_suggestion.confidence,
            "reason": top_suggestion.reason,
            "alternatives": [s.to_dict() for s in suggestions[1:]]
        }
        
        invoice.ai_booking_suggestion = suggestion_dict
        invoice.ai_confidence_score = top_suggestion.confidence
        invoice.ai_detected_category = f"Account {top_suggestion.account_number}"
        invoice.ai_processed = True
        invoice.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(invoice)
        
        return suggestion_dict


# Helper function for easy import
async def suggest_account_for_invoice(
    db: AsyncSession,
    invoice_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """
    Convenience function to get account suggestions for an invoice
    
    Returns list of suggestion dicts
    """
    service = AICategorizationService(db)
    
    result = await db.execute(
        select(VendorInvoice).where(VendorInvoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        return []
    
    suggestions = await service.suggest_account(invoice)
    return [s.to_dict() for s in suggestions]
