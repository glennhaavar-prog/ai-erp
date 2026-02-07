"""
Intent Classifier - NLP with Claude API
Classifies user intent and extracts entities
"""
import logging
import json
from typing import Dict, Any, Optional
import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies chat messages into intents using Claude API
    
    Supported intents:
    - book_invoice: User wants to book an invoice
    - show_invoice: Show invoice details
    - invoice_status: Query invoice(s) status
    - approve_booking: Approve a booking
    - correct_booking: Correct/modify a booking
    - list_invoices: List invoices (pending, recent, etc.)
    - help: Request help
    - general: General conversation
    """
    
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set - IntentClassifier will use fallback")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        self.model = settings.CLAUDE_MODEL
    
    async def classify(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify user message into intent + entities
        
        Args:
            message: User's message
            context: Conversation context (current invoice, client, etc.)
        
        Returns:
            {
                'intent': 'book_invoice',
                'confidence': 0.95,
                'entities': {
                    'invoice_number': 'INV-12345',
                    'account': '6340',
                    'confirmation': True
                },
                'reasoning': 'User wants to book invoice...'
            }
        """
        
        if not self.client:
            # Fallback to simple keyword matching
            return self._fallback_classify(message, context)
        
        try:
            # Build context string
            context_str = ""
            if context:
                context_str = f"""
Current conversation context:
- Current invoice: {context.get('current_invoice_id', 'None')}
- Client ID: {context.get('client_id', 'Unknown')}
- Previous intent: {context.get('last_intent', 'None')}
- Conversation history: {len(context.get('conversation_history', []))} messages
"""
            
            # Build prompt
            prompt = f"""{context_str}

User message: "{message}"

Classify this message into ONE of these intents:
1. book_invoice - User wants to book/post an invoice
2. show_invoice - User wants to see invoice details
3. invoice_status - User asks about invoice status (one or multiple)
4. approve_booking - User wants to approve a suggested booking
5. correct_booking - User wants to correct/change account or booking
6. list_invoices - User wants to list invoices (pending, low confidence, etc.)
7. help - User asks for help or available commands
8. general - General question or conversation

Also extract relevant entities:
- invoice_number (e.g., "INV-12345", "faktura 100")
- invoice_id (UUID if mentioned)
- account_number (e.g., "6340", "konto 6300")
- confirmation (true/false if user says yes/no/ja/nei)
- filter (e.g., "low confidence", "pending", "today")

Return ONLY a JSON object:
{{
    "intent": "intent_name",
    "confidence": 0.0-1.0,
    "entities": {{
        "invoice_number": "...",
        "account_number": "...",
        "confirmation": true/false,
        "filter": "..."
    }},
    "reasoning": "Brief explanation"
}}"""
            
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            response_text = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
            
            result = json.loads(response_text)
            
            logger.info(f"Intent classified: {result.get('intent')} (confidence: {result.get('confidence')})")
            
            return result
        
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            # Fallback to simple keyword matching
            return self._fallback_classify(message, context)
    
    def _fallback_classify(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simple keyword-based classification when Claude is unavailable
        """
        msg_lower = message.lower().strip()
        
        # Extract entities
        entities = {}
        
        # Check for invoice number
        import re
        inv_match = re.search(r'inv[- ]?(\d+)', msg_lower)
        if inv_match:
            entities['invoice_number'] = f"INV-{inv_match.group(1)}"
        
        # Check for account number
        acc_match = re.search(r'(?:konto|account)\s*(\d{4})', msg_lower)
        if acc_match:
            entities['account_number'] = acc_match.group(1)
        elif re.search(r'\b(\d{4})\b', msg_lower):
            entities['account_number'] = re.search(r'\b(\d{4})\b', msg_lower).group(1)
        
        # Check for confirmation
        if any(word in msg_lower for word in ['ja', 'yes', 'ok', 'godkjenn', 'approve']):
            entities['confirmation'] = True
        elif any(word in msg_lower for word in ['nei', 'no', 'avbryt', 'cancel']):
            entities['confirmation'] = False
        
        # Check for filters
        if 'lav confidence' in msg_lower or 'low confidence' in msg_lower:
            entities['filter'] = 'low_confidence'
        elif 'venter' in msg_lower or 'pending' in msg_lower:
            entities['filter'] = 'pending'
        
        # Classify intent
        if any(word in msg_lower for word in ['bokfør', 'book', 'post faktura', 'legg til']):
            intent = 'book_invoice'
        elif any(word in msg_lower for word in ['vis', 'show', 'se', 'detaljer', 'details']):
            if 'faktura' in msg_lower or 'invoice' in msg_lower:
                intent = 'show_invoice'
            else:
                intent = 'list_invoices'
        elif any(word in msg_lower for word in ['status', 'oversikt', 'overview']):
            intent = 'invoice_status'
        elif any(word in msg_lower for word in ['godkjenn', 'approve']):
            intent = 'approve_booking'
        elif any(word in msg_lower for word in ['korriger', 'correct', 'endre', 'change', 'bruk konto']):
            intent = 'correct_booking'
        elif any(word in msg_lower for word in ['hjelp', 'help', 'kommandoer', 'commands']):
            intent = 'help'
        else:
            intent = 'general'
        
        return {
            'intent': intent,
            'confidence': 0.7,  # Lower confidence for fallback
            'entities': entities,
            'reasoning': 'Fallback keyword matching (Claude unavailable)'
        }
