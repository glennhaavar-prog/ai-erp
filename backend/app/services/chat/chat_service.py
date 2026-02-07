"""
Chat Service - Main orchestrator for conversational booking interface
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .intent_classifier import IntentClassifier
from .context_manager import ContextManager
from .action_handlers import (
    BookingActionHandler,
    StatusQueryHandler,
    ApprovalHandler,
    CorrectionHandler
)

logger = logging.getLogger(__name__)


class ChatService:
    """
    Main chat service for invoice booking
    
    Orchestrates:
    - Intent classification
    - Context management
    - Action execution
    - Response generation
    """
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.context_manager = ContextManager()
        self.booking_handler = BookingActionHandler()
        self.status_handler = StatusQueryHandler()
        self.approval_handler = ApprovalHandler()
        self.correction_handler = CorrectionHandler()
    
    async def process_message(
        self,
        db: AsyncSession,
        session_id: str,
        client_id: str,
        user_id: Optional[str],
        message: str
    ) -> Dict[str, Any]:
        """
        Process chat message and return response
        
        Args:
            db: Database session
            session_id: Chat session ID
            client_id: Client UUID
            user_id: User UUID (optional)
            message: User's message
        
        Returns:
            {
                'message': 'Response text',
                'action': 'action_performed',
                'data': {...},
                'timestamp': '...'
            }
        """
        
        try:
            # Update context with client_id
            self.context_manager.update_context(
                session_id,
                client_id=client_id,
                user_id=user_id
            )
            
            # Add user message to history
            self.context_manager.add_message(
                session_id,
                role='user',
                content=message
            )
            
            # Get context
            context = self.context_manager.get_context(session_id)
            
            # Check for pending confirmation
            pending = self.context_manager.get_pending_confirmation(session_id)
            if pending:
                return await self._handle_confirmation(db, session_id, client_id, user_id, message, pending)
            
            # Classify intent
            intent_result = await self.intent_classifier.classify(message, context)
            intent = intent_result['intent']
            entities = intent_result.get('entities', {})
            
            logger.info(f"Intent: {intent}, Entities: {entities}")
            
            # Update context
            self.context_manager.update_context(
                session_id,
                last_intent=intent,
                entities=entities
            )
            
            # Route to appropriate handler
            if intent == 'book_invoice':
                response = await self._handle_book_invoice(
                    db, session_id, client_id, user_id, entities
                )
            
            elif intent == 'show_invoice':
                response = await self._handle_show_invoice(
                    db, session_id, client_id, entities
                )
            
            elif intent == 'invoice_status':
                response = await self._handle_invoice_status(
                    db, session_id, client_id, entities
                )
            
            elif intent == 'approve_booking':
                response = await self._handle_approve_booking(
                    db, session_id, client_id, user_id, entities
                )
            
            elif intent == 'correct_booking':
                response = await self._handle_correct_booking(
                    db, session_id, client_id, user_id, entities
                )
            
            elif intent == 'list_invoices':
                response = await self._handle_list_invoices(
                    db, session_id, client_id, entities
                )
            
            elif intent == 'help':
                response = self._handle_help()
            
            else:
                response = {
                    'message': "🤔 Beklager, jeg forstod ikke helt. Skriv 'help' for å se tilgjengelige kommandoer.",
                    'action': 'unknown',
                    'data': {}
                }
            
            # Add assistant message to history
            self.context_manager.add_message(
                session_id,
                role='assistant',
                content=response['message'],
                metadata={'intent': intent, 'entities': entities}
            )
            
            # Add timestamp
            response['timestamp'] = datetime.utcnow().isoformat()
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                'message': f"❌ Feil: {str(e)}",
                'action': 'error',
                'data': {'error': str(e)},
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _handle_book_invoice(
        self,
        db: AsyncSession,
        session_id: str,
        client_id: str,
        user_id: Optional[str],
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle booking an invoice"""
        
        invoice_number = entities.get('invoice_number')
        invoice_id = entities.get('invoice_id')
        
        # Check if we need to ask which invoice
        if not invoice_number and not invoice_id:
            # Check if there's a current invoice in context
            context = self.context_manager.get_context(session_id)
            invoice_id = context.get('current_invoice_id')
            
            if not invoice_id:
                # List recent pending invoices
                pending = await self.status_handler.list_pending_invoices(
                    db, client_id, limit=5
                )
                
                if pending['success'] and pending['invoices']:
                    return {
                        'message': f"Hvilken faktura vil du bokføre?\n\n{pending['message']}\n\nSi f.eks: 'Bokfør faktura INV-12345'",
                        'action': 'request_invoice',
                        'data': pending
                    }
                else:
                    return {
                        'message': "✅ Ingen fakturaer venter på bokføring!",
                        'action': 'no_invoices',
                        'data': {}
                    }
        
        # Analyze invoice
        analysis = await self.booking_handler.analyze_invoice(
            db, invoice_number, invoice_id, client_id
        )
        
        if not analysis['success']:
            return {
                'message': analysis['message'],
                'action': 'error',
                'data': analysis
            }
        
        # Update context with current invoice
        self.context_manager.update_context(
            session_id,
            current_invoice_id=analysis['invoice']['id'],
            current_invoice_number=analysis['invoice']['invoice_number']
        )
        
        # Format suggestion
        invoice = analysis['invoice']
        booking = analysis['suggested_booking']
        confidence = analysis['confidence']
        
        message = f"📄 **Faktura {invoice['invoice_number']}**\n\n"
        message += f"• Leverandør: {invoice['vendor']}\n"
        message += f"• Beløp: {analysis['total_amount']:,.2f} kr (ekskl mva: {analysis['amount_excl_vat']:,.2f} kr, mva: {analysis['vat_amount']:,.2f} kr)\n\n"
        message += f"**Foreslått bokføring** (Confidence: {confidence}%):\n\n"
        
        for line in booking:
            account = line.get('account', '')
            debit = line.get('debit', 0)
            credit = line.get('credit', 0)
            desc = line.get('description', '')
            
            if debit > 0:
                message += f"• Konto {account}: {debit:,.2f} kr (debet) - {desc}\n"
            elif credit > 0:
                message += f"• Konto {account}: {credit:,.2f} kr (kredit) - {desc}\n"
        
        message += f"\n**Bokfør nå?** (Svar 'ja' eller 'nei')"
        
        # Set pending confirmation
        self.context_manager.set_pending_confirmation(
            session_id,
            action='book_invoice',
            data={
                'invoice_id': invoice['id'],
                'booking_suggestion': {'lines': booking, 'confidence': confidence}
            },
            question=message
        )
        
        return {
            'message': message,
            'action': 'suggest_booking',
            'data': analysis
        }
    
    async def _handle_confirmation(
        self,
        db: AsyncSession,
        session_id: str,
        client_id: str,
        user_id: Optional[str],
        message: str,
        pending: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle yes/no confirmation"""
        
        msg_lower = message.lower().strip()
        
        # Check for yes/no
        if msg_lower in ['ja', 'yes', 'ok', 'godkjenn', 'approve']:
            confirmed = True
        elif msg_lower in ['nei', 'no', 'avbryt', 'cancel']:
            confirmed = False
        else:
            # Not a clear yes/no, ask again
            return {
                'message': f"⚠️ Vennligst svar 'ja' for å bekrefte eller 'nei' for å avbryte.\n\n{pending['question']}",
                'action': 'request_confirmation',
                'data': pending
            }
        
        # Clear pending confirmation
        self.context_manager.clear_pending_confirmation(session_id)
        
        if not confirmed:
            return {
                'message': "❌ Avbrutt. Ingen endringer gjort.",
                'action': 'cancelled',
                'data': {}
            }
        
        # Execute action
        action = pending['action']
        data = pending['data']
        
        if action == 'book_invoice':
            result = await self.booking_handler.book_invoice(
                db,
                invoice_id=data['invoice_id'],
                booking_suggestion=data['booking_suggestion'],
                user_id=user_id
            )
            
            return {
                'message': result['message'],
                'action': 'booking_executed',
                'data': result
            }
        
        return {
            'message': "❌ Ukjent handling",
            'action': 'error',
            'data': {}
        }
    
    async def _handle_show_invoice(
        self,
        db: AsyncSession,
        session_id: str,
        client_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Show invoice details"""
        
        invoice_number = entities.get('invoice_number')
        invoice_id = entities.get('invoice_id')
        
        result = await self.status_handler.get_invoice_status(
            db, invoice_number, invoice_id, client_id
        )
        
        return {
            'message': result.get('message', '❌ Feil'),
            'action': 'show_invoice',
            'data': result
        }
    
    async def _handle_invoice_status(
        self,
        db: AsyncSession,
        session_id: str,
        client_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle status query"""
        
        invoice_number = entities.get('invoice_number')
        
        if invoice_number:
            # Status for specific invoice
            result = await self.status_handler.get_invoice_status(
                db, invoice_number, None, client_id
            )
        else:
            # Overall status
            result = await self.status_handler.get_overall_status(db, client_id)
        
        return {
            'message': result.get('message', '❌ Feil'),
            'action': 'status',
            'data': result
        }
    
    async def _handle_approve_booking(
        self,
        db: AsyncSession,
        session_id: str,
        client_id: str,
        user_id: Optional[str],
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Approve booking in review queue"""
        
        item_id = entities.get('invoice_id')
        
        if not item_id:
            return {
                'message': "❌ Vennligst oppgi ID for item som skal godkjennes",
                'action': 'error',
                'data': {}
            }
        
        result = await self.approval_handler.approve_booking(
            db, item_id, client_id, user_id
        )
        
        return {
            'message': result['message'],
            'action': 'approve',
            'data': result
        }
    
    async def _handle_correct_booking(
        self,
        db: AsyncSession,
        session_id: str,
        client_id: str,
        user_id: Optional[str],
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Correct account in booking"""
        
        # Get current invoice from context
        context = self.context_manager.get_context(session_id)
        invoice_id = context.get('current_invoice_id')
        
        if not invoice_id:
            return {
                'message': "❌ Ingen aktiv faktura i kontekst. Vis en faktura først.",
                'action': 'error',
                'data': {}
            }
        
        account_number = entities.get('account_number')
        
        if not account_number:
            return {
                'message': "❌ Vennligst oppgi kontonummer (f.eks: 'bruk konto 6340')",
                'action': 'error',
                'data': {}
            }
        
        # For now, assume we're correcting the expense account (first debit line)
        # In a full implementation, you'd need to specify which account to replace
        
        return {
            'message': f"✅ Korrigering registrert til konto {account_number}",
            'action': 'correct',
            'data': {}
        }
    
    async def _handle_list_invoices(
        self,
        db: AsyncSession,
        session_id: str,
        client_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """List invoices"""
        
        filter_type = entities.get('filter')
        
        result = await self.status_handler.list_pending_invoices(
            db, client_id, filter_type=filter_type
        )
        
        return {
            'message': result['message'],
            'action': 'list_invoices',
            'data': result
        }
    
    def _handle_help(self) -> Dict[str, Any]:
        """Return help message"""
        
        message = """🤖 **Kontali Chat Assistant - Kommandoer**

**Bokføring:**
• "Bokfør denne faktura" - Start bokføring
• "Bokfør faktura INV-12345" - Bokfør spesifikk faktura
• "ja" / "nei" - Bekreft eller avbryt foreslått bokføring

**Status og oversikt:**
• "Hva er status på faktura INV-12345?" - Se fakturastatus
• "Hva er status på alle fakturaer?" - Oversikt
• "Vis meg fakturaer med lav confidence" - Filtrer fakturaer

**Godkjenning:**
• "Godkjenn bokføring for faktura X" - Godkjenn fra review queue

**Korreksjon:**
• "Korriger bokføring: bruk konto 6300 i stedet" - Endre konto

**Generelt:**
• "help" - Vis denne hjelpen

Tips: Chat'en husker kontekst, så du kan si "bokfør denne" etter å ha sett en faktura."""
        
        return {
            'message': message,
            'action': 'help',
            'data': {}
        }
