"""
Context Manager - Track conversation state
Manages session context for multi-turn conversations
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context for chat sessions
    
    Context includes:
    - Current invoice being discussed
    - Client ID
    - Conversation history (last N messages)
    - Last intent
    - Pending confirmations (e.g., "Do you want to book this?")
    """
    
    def __init__(self, max_history: int = 10, session_timeout_minutes: int = 30):
        """
        Initialize context manager
        
        Args:
            max_history: Maximum messages to keep in history
            session_timeout_minutes: Auto-clear context after this time
        """
        self.max_history = max_history
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
        # In-memory store (in production, use Redis or database)
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get current context for session
        
        Returns:
            {
                'session_id': '...',
                'user_id': '...',
                'client_id': '...',
                'current_invoice_id': '...',
                'current_invoice_number': '...',
                'conversation_history': [...],
                'last_intent': '...',
                'pending_confirmation': {...},
                'entities': {...},
                'last_activity': '...'
            }
        """
        session = self._sessions.get(session_id)
        
        # Check if session expired
        if session:
            last_activity = session.get('last_activity')
            if last_activity:
                if datetime.utcnow() - last_activity > self.session_timeout:
                    logger.info(f"Session {session_id} expired, clearing context")
                    self.clear_context(session_id)
                    session = None
        
        # Return existing or new context
        if not session:
            session = self._create_new_context(session_id)
        
        return session
    
    def update_context(
        self,
        session_id: str,
        **updates
    ) -> Dict[str, Any]:
        """
        Update context with new values
        
        Args:
            session_id: Session ID
            **updates: Key-value pairs to update (e.g., current_invoice_id='...')
        
        Returns:
            Updated context
        """
        context = self.get_context(session_id)
        
        # Update fields
        for key, value in updates.items():
            context[key] = value
        
        # Update last activity
        context['last_activity'] = datetime.utcnow()
        
        self._sessions[session_id] = context
        
        logger.debug(f"Context updated for session {session_id}: {list(updates.keys())}")
        
        return context
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add message to conversation history
        
        Args:
            session_id: Session ID
            role: 'user' or 'assistant'
            content: Message content
            metadata: Additional metadata (intent, entities, etc.)
        """
        context = self.get_context(session_id)
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        history = context.get('conversation_history', [])
        history.append(message)
        
        # Keep only last N messages
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        
        context['conversation_history'] = history
        context['last_activity'] = datetime.utcnow()
        
        self._sessions[session_id] = context
    
    def set_pending_confirmation(
        self,
        session_id: str,
        action: str,
        data: Dict[str, Any],
        question: str
    ):
        """
        Set a pending confirmation (e.g., "Do you want to book this invoice?")
        
        Args:
            session_id: Session ID
            action: Action name (e.g., 'book_invoice')
            data: Data needed to execute action (e.g., invoice_id, booking_lines)
            question: Question text shown to user
        """
        context = self.get_context(session_id)
        
        context['pending_confirmation'] = {
            'action': action,
            'data': data,
            'question': question,
            'set_at': datetime.utcnow().isoformat()
        }
        
        self._sessions[session_id] = context
        
        logger.info(f"Pending confirmation set for session {session_id}: {action}")
    
    def get_pending_confirmation(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get pending confirmation if any
        
        Returns:
            Confirmation dict or None
        """
        context = self.get_context(session_id)
        return context.get('pending_confirmation')
    
    def clear_pending_confirmation(self, session_id: str):
        """Clear pending confirmation"""
        context = self.get_context(session_id)
        if 'pending_confirmation' in context:
            del context['pending_confirmation']
            self._sessions[session_id] = context
    
    def clear_context(self, session_id: str):
        """Clear all context for session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Context cleared for session {session_id}")
    
    def _create_new_context(self, session_id: str) -> Dict[str, Any]:
        """Create new empty context"""
        context = {
            'session_id': session_id,
            'user_id': None,
            'client_id': None,
            'current_invoice_id': None,
            'current_invoice_number': None,
            'conversation_history': [],
            'last_intent': None,
            'pending_confirmation': None,
            'entities': {},
            'last_activity': datetime.utcnow()
        }
        
        self._sessions[session_id] = context
        
        return context
    
    def get_recent_invoices(self, session_id: str, limit: int = 5) -> List[str]:
        """
        Get list of recently mentioned invoice IDs
        
        Returns:
            List of invoice IDs (most recent first)
        """
        context = self.get_context(session_id)
        history = context.get('conversation_history', [])
        
        invoice_ids = []
        
        for message in reversed(history):
            metadata = message.get('metadata', {})
            entities = metadata.get('entities', {})
            
            invoice_id = entities.get('invoice_id')
            if invoice_id and invoice_id not in invoice_ids:
                invoice_ids.append(invoice_id)
            
            if len(invoice_ids) >= limit:
                break
        
        return invoice_ids
