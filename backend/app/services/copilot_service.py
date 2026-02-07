"""
Copilot Service - AI Assistant for Accountants

Context-aware AI assistant that helps accountants with:
- Answering accounting questions
- Analyzing Review Queue items
- Suggesting bookings and accruals
- Explaining account codes
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.review_queue import ReviewQueue
from app.models.chart_of_accounts import Account
from app.models.accrual import Accrual
from app.config import settings
import anthropic


class CopilotService:
    """AI Copilot - Context-aware assistant for accountants"""
    
    def __init__(self):
        # Get API key from settings
        api_key = settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else None
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5"
    
    async def chat(
        self,
        message: str,
        context: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process chat message with context.
        
        Args:
            message: User's question/message
            context: Current context (page, item_id, client_id)
            db: Database session
        
        Returns:
            Dict with response and optional suggestions
        """
        
        # Build context-aware system prompt
        system_prompt = await self._build_system_prompt(context, db)
        
        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": message}
            ]
        )
        
        response_text = response.content[0].text
        
        # Extract suggestions from response (if any)
        suggestions = self._extract_suggestions(response_text)
        
        return {
            "response": response_text,
            "suggestions": suggestions
        }
    
    async def suggest(
        self,
        context: str,
        item_id: Optional[UUID],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get proactive suggestions based on context.
        
        Args:
            context: Context type (review_queue, hovedbok, accruals)
            item_id: Optional item ID to analyze
            db: Database session
        
        Returns:
            Dict with suggestions list
        """
        
        suggestions = []
        
        if context == "review_queue" and item_id:
            # Fetch review queue item
            result = await db.execute(
                select(ReviewQueue).where(ReviewQueue.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if item:
                # Analyze and suggest
                if item.ai_confidence_score and item.ai_confidence_score < 70:
                    suggestions.append({
                        "type": "warning",
                        "text": "AI er usikker på denne bokføringen (confidence: {}%). Sjekk nøye.".format(item.ai_confidence_score),
                        "action": None
                    })
                
                # Check if should be accrued
                if item.ai_booking_suggestion:
                    description = item.ai_booking_suggestion.get("description", "").lower()
                    if any(kw in description for kw in ["forsikring", "abonnement", "lisens", "leie"]):
                        suggestions.append({
                            "type": "tip",
                            "text": "Dette kan være en periodiseringskostnad. Vurder å opprette periodisering.",
                            "action": "create_accrual",
                            "action_data": {"item_id": str(item.id)}
                        })
        
        elif context == "accruals":
            # General accrual tips
            suggestions.append({
                "type": "tip",
                "text": "Periodiseringer hjelper deg å fordele kostnader over tid. Typiske eksempler: forsikring, leie, abonnementer.",
                "action": None
            })
        
        return {
            "suggestions": suggestions
        }
    
    async def _build_system_prompt(self, context: Dict[str, Any], db: AsyncSession) -> str:
        """
        Build context-aware system prompt for Claude.
        
        Args:
            context: Context dict with page, item_id, client_id
            db: Database session
        
        Returns:
            System prompt string
        """
        
        base_prompt = """Du er en AI regnskapsassistent for Kontali ERP.
        
Din jobb er å hjelpe regnskapsførere med:
- Forklare kontoer og MVA-koder
- Analysere fakturaer og foreslå bokføring
- Veilede om periodisering og tidsavgrensning
- Svare på spørsmål om norsk bokføring og MVA

Svar alltid på norsk (bokmål).
Vær konsis og praktisk.
Hvis du er usikker, si det.
Følg norsk regnskapsstandard (NS 4102) og bokføringsloven.
"""
        
        # Add context-specific information
        page = context.get("page")
        
        if page == "review_queue":
            base_prompt += "\n\nBrukeren ser på Review Queue (bokføringskø)."
            
            item_id = context.get("item_id")
            if item_id:
                # Fetch item details
                result = await db.execute(
                    select(ReviewQueue).where(ReviewQueue.id == UUID(item_id))
                )
                item = result.scalar_one_or_none()
                
                if item:
                    base_prompt += f"\n\nAktuell faktura:"
                    base_prompt += f"\n- Beløp: {item.amount} NOK"
                    if item.ai_booking_suggestion:
                        base_prompt += f"\n- AI-forslag: {item.ai_booking_suggestion}"
                    if item.ai_confidence_score:
                        base_prompt += f"\n- AI confidence: {item.ai_confidence_score}%"
        
        elif page == "accruals":
            base_prompt += "\n\nBrukeren ser på Periodisering (tidsavgrensning av kostnader/inntekter)."
        
        elif page == "hovedbok":
            base_prompt += "\n\nBrukeren ser på Hovedbok (journal entries)."
        
        return base_prompt
    
    def _extract_suggestions(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract actionable suggestions from AI response.
        
        Looks for patterns like:
        - "Du bør..."
        - "Jeg foreslår..."
        - "Vurder å..."
        
        Returns list of suggestion dicts.
        """
        
        suggestions = []
        
        # Simple pattern matching (can be enhanced)
        suggestion_keywords = ["du bør", "jeg foreslår", "vurder å", "anbefaler"]
        
        lines = response_text.lower().split("\n")
        for line in lines:
            if any(kw in line for kw in suggestion_keywords):
                suggestions.append({
                    "type": "tip",
                    "text": line.strip(),
                    "action": None
                })
        
        return suggestions
