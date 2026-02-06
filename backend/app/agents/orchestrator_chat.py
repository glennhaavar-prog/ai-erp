"""
Orchestrator Chat Agent - Conversational interface for review queue management
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func, cast, String
from uuid import UUID

from app.agents.base import BaseAgent
from app.models.review_queue import ReviewQueue, ReviewStatus, ReviewPriority, IssueCategory
from app.models.vendor_invoice import VendorInvoice
from app.models.general_ledger import GeneralLedger
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)


class OrchestratorChatAgent(BaseAgent):
    """
    Conversational AI agent for review queue management
    
    Capabilities:
    - Show review queue items with context
    - Approve/reject items via natural language
    - Answer questions about status and workload
    - Provide suggestions and insights
    """
    
    def __init__(self):
        super().__init__(agent_type="orchestrator_chat")
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for Claude"""
        return """You are an AI assistant for the Kontali ERP system, specializing in helping accountants review and approve financial transactions.

Your capabilities:
1. Show pending review queue items
2. Approve or reject items based on user commands
3. Provide detailed information about transactions
4. Answer questions about workload and status

When responding:
- Be concise and professional
- Use accounting terminology appropriately
- For review items, always include: ID, amount, vendor, confidence score, and reason for review
- When approving/rejecting, confirm the action clearly
- If unsure about a command, ask for clarification

Available actions:
- "show review queue" / "what's in the queue?" → List pending items
- "approve [id]" / "reject [id]" → Approve or reject specific item
- "show details [id]" → Show full details of an item
- "what's my workload?" → Show statistics

Always structure responses in a clear, scannable format."""
    
    async def chat(
        self,
        db: AsyncSession,
        client_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Main chat interface
        
        Args:
            db: Database session
            client_id: Client UUID
            user_message: User's message
            conversation_history: Previous messages for context
        
        Returns:
            Response dictionary with message and any actions taken
        """
        logger.info(f"OrchestratorChat: Processing message for client {client_id}")
        
        # Parse intent and extract entities
        intent = await self._detect_intent(user_message)
        
        # Handle different intents
        if intent["type"] == "show_queue":
            return await self._handle_show_queue(db, client_id)
        
        elif intent["type"] == "approve":
            item_id = intent.get("item_id")
            if not item_id:
                return self._error_response("Please specify which item to approve (e.g., 'approve <id>')")
            return await self._handle_approve(db, client_id, item_id)
        
        elif intent["type"] == "reject":
            item_id = intent.get("item_id")
            reason = intent.get("reason")
            if not item_id:
                return self._error_response("Please specify which item to reject (e.g., 'reject <id>')")
            return await self._handle_reject(db, client_id, item_id, reason)
        
        elif intent["type"] == "show_details":
            item_id = intent.get("item_id")
            if not item_id:
                return self._error_response("Please specify which item to show (e.g., 'show details <id>')")
            return await self._handle_show_details(db, client_id, item_id)
        
        elif intent["type"] == "workload":
            return await self._handle_workload(db, client_id)
        
        else:
            # General query - use Claude for contextual response
            return await self._handle_general_query(db, client_id, user_message, conversation_history)
    
    async def _detect_intent(self, message: str) -> Dict[str, Any]:
        """
        Detect user intent from message
        
        Returns:
            Dictionary with intent type and extracted entities
        """
        message_lower = message.lower().strip()
        
        # Show queue
        if any(phrase in message_lower for phrase in ["show queue", "list queue", "what's in the queue", "pending items", "review queue"]):
            return {"type": "show_queue"}
        
        # Approve
        if message_lower.startswith("approve"):
            item_id = self._extract_uuid(message)
            return {"type": "approve", "item_id": item_id}
        
        # Reject
        if message_lower.startswith("reject"):
            item_id = self._extract_uuid(message)
            # Extract reason if provided after the ID
            reason_match = message.split(str(item_id))[-1].strip() if item_id else None
            return {"type": "reject", "item_id": item_id, "reason": reason_match}
        
        # Show details
        if any(phrase in message_lower for phrase in ["show details", "details for", "info about", "show item"]):
            item_id = self._extract_uuid(message)
            return {"type": "show_details", "item_id": item_id}
        
        # Workload
        if any(phrase in message_lower for phrase in ["workload", "how many", "statistics", "stats", "overview"]):
            return {"type": "workload"}
        
        # General query
        return {"type": "general"}
    
    def _extract_uuid(self, message: str) -> Optional[str]:
        """Extract UUID from message (full or partial)"""
        import re
        # Try full UUID first
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        match = re.search(uuid_pattern, message.lower())
        if match:
            return match.group(0)
        
        # Try partial UUID (at least 8 hex chars)
        partial_pattern = r'\b[0-9a-f]{8,}\b'
        match = re.search(partial_pattern, message.lower())
        return match.group(0) if match else None
    
    async def _fetch_item_by_id(
        self,
        db: AsyncSession,
        client_id: str,
        item_id: str
    ) -> Optional[ReviewQueue]:
        """Fetch review queue item by full or partial ID"""
        # Build query based on whether we have a full or partial UUID
        if len(item_id) == 36:
            # Full UUID - try exact match
            try:
                result = await db.execute(
                    select(ReviewQueue).where(
                        ReviewQueue.client_id == UUID(client_id),
                        ReviewQueue.id == UUID(item_id)
                    )
                )
                return result.scalar_one_or_none()
            except ValueError:
                pass  # Fall through to partial match
        
        # Partial UUID - match by string prefix
        result = await db.execute(
            select(ReviewQueue).where(
                ReviewQueue.client_id == UUID(client_id),
                cast(ReviewQueue.id, String).like(f"{item_id}%")
            )
        )
        return result.scalar_one_or_none()
    
    async def _handle_show_queue(
        self,
        db: AsyncSession,
        client_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Show pending review queue items"""
        
        # Fetch pending items
        result = await db.execute(
            select(ReviewQueue)
            .where(
                ReviewQueue.client_id == UUID(client_id),
                cast(ReviewQueue.status, String) == 'PENDING'
            )
            .order_by(desc(ReviewQueue.priority), ReviewQueue.created_at)
            .limit(limit)
        )
        items = result.scalars().all()
        
        if not items:
            return {
                "message": "✅ Great! Your review queue is empty. No items need attention right now.",
                "action": None,
                "data": {"count": 0, "items": []}
            }
        
        # Build formatted response
        response = f"📋 **Review Queue** ({len(items)} pending items)\n\n"
        
        items_data = []
        for idx, item in enumerate(items, 1):
            # Get source details
            source_details = await self._get_source_details(db, item)
            
            priority_emoji = {
                ReviewPriority.URGENT: "🔴",
                ReviewPriority.HIGH: "🟠",
                ReviewPriority.MEDIUM: "🟡",
                ReviewPriority.LOW: "🟢"
            }.get(item.priority, "⚪")
            
            response += f"{priority_emoji} **#{idx}** `{str(item.id)[:8]}`\n"
            response += f"   • **Amount:** {source_details.get('amount', 'N/A')}\n"
            response += f"   • **Vendor:** {source_details.get('vendor', 'Unknown')}\n"
            response += f"   • **Confidence:** {item.ai_confidence}%\n"
            response += f"   • **Issue:** {item.issue_description}\n"
            response += f"   • **Created:** {item.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            items_data.append({
                "id": str(item.id),
                "priority": item.priority.value,
                "confidence": item.ai_confidence,
                "issue": item.issue_description,
                **source_details
            })
        
        response += f"\n💡 **Commands:**\n"
        response += f"• `approve <id>` - Approve an item\n"
        response += f"• `reject <id> [reason]` - Reject an item\n"
        response += f"• `show details <id>` - View full details"
        
        return {
            "message": response,
            "action": "list_queue",
            "data": {"count": len(items), "items": items_data}
        }
    
    async def _handle_approve(
        self,
        db: AsyncSession,
        client_id: str,
        item_id: str
    ) -> Dict[str, Any]:
        """Approve a review queue item"""        
        
        try:
            # Fetch item
            item = await self._fetch_item_by_id(db, client_id, item_id)
            
            if not item:
                return self._error_response(f"Item `{item_id}` not found or doesn't belong to your client.")
            
            if str(item.status.value) != "pending":
                return self._error_response(f"Item `{item_id[:8]}` has already been {item.status.value}.")
            
            # Update review queue item
            await db.execute(
                update(ReviewQueue)
                .where(ReviewQueue.id == UUID(item_id))
                .values(
                    status='approved',
                    resolved_at=datetime.utcnow(),
                    resolution_notes="Approved via chat interface"
                )
            )
            
            # If source is general_ledger, post the entry
            if item.source_type == "general_ledger":
                await db.execute(
                    update(GeneralLedger)
                    .where(GeneralLedger.id == item.source_id)
                    .values(status='posted')
                )
            
            await db.commit()
            
            # Get details for confirmation
            source_details = await self._get_source_details(db, item)
            
            response = f"✅ **Approved** `{item_id[:8]}`\n\n"
            response += f"• **Amount:** {source_details.get('amount', 'N/A')}\n"
            response += f"• **Vendor:** {source_details.get('vendor', 'Unknown')}\n"
            response += f"• **Status:** Posted to ledger\n"
            
            logger.info(f"OrchestratorChat: Approved item {item_id}")
            
            return {
                "message": response,
                "action": "approve",
                "data": {"item_id": item_id, "status": "approved"}
            }
            
        except Exception as e:
            logger.error(f"OrchestratorChat: Error approving item {item_id}: {str(e)}")
            return self._error_response(f"Error approving item: {str(e)}")
    
    async def _handle_reject(
        self,
        db: AsyncSession,
        client_id: str,
        item_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject a review queue item"""        
        
        try:
            # Fetch item
            item = await self._fetch_item_by_id(db, client_id, item_id)
            
            if not item:
                return self._error_response(f"Item `{item_id}` not found or doesn't belong to your client.")
            
            if str(item.status.value) != "pending":
                return self._error_response(f"Item `{item_id[:8]}` has already been {item.status.value}.")
            
            # Update review queue item
            notes = f"Rejected via chat interface. Reason: {reason}" if reason else "Rejected via chat interface"
            
            await db.execute(
                update(ReviewQueue)
                .where(ReviewQueue.id == UUID(item_id))
                .values(
                    status='rejected',
                    resolved_at=datetime.utcnow(),
                    resolution_notes=notes
                )
            )
            
            # If source is general_ledger, mark as rejected
            if item.source_type == "general_ledger":
                await db.execute(
                    update(GeneralLedger)
                    .where(GeneralLedger.id == item.source_id)
                    .values(status='rejected')
                )
            
            await db.commit()
            
            # Get details for confirmation
            source_details = await self._get_source_details(db, item)
            
            response = f"❌ **Rejected** `{item_id[:8]}`\n\n"
            response += f"• **Amount:** {source_details.get('amount', 'N/A')}\n"
            response += f"• **Vendor:** {source_details.get('vendor', 'Unknown')}\n"
            if reason:
                response += f"• **Reason:** {reason}\n"
            
            logger.info(f"OrchestratorChat: Rejected item {item_id}")
            
            return {
                "message": response,
                "action": "reject",
                "data": {"item_id": item_id, "status": "rejected", "reason": reason}
            }
            
        except Exception as e:
            logger.error(f"OrchestratorChat: Error rejecting item {item_id}: {str(e)}")
            return self._error_response(f"Error rejecting item: {str(e)}")
    
    async def _handle_show_details(
        self,
        db: AsyncSession,
        client_id: str,
        item_id: str
    ) -> Dict[str, Any]:
        """Show detailed information about a review queue item"""
        
        try:
            # Fetch item
            item = await self._fetch_item_by_id(db, client_id, item_id)
            
            if not item:
                return self._error_response(f"Item `{item_id}` not found.")
            
            # Get source details
            source_details = await self._get_source_details(db, item)
            
            response = f"📄 **Item Details** `{item_id[:8]}`\n\n"
            response += f"**Status:** {item.status.value.upper()}\n"
            response += f"**Priority:** {item.priority.value.upper()}\n"
            response += f"**Created:** {item.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            response += f"**Source Information:**\n"
            response += f"• Type: {item.source_type}\n"
            response += f"• Amount: {source_details.get('amount', 'N/A')}\n"
            response += f"• Vendor: {source_details.get('vendor', 'Unknown')}\n"
            response += f"• Date: {source_details.get('date', 'N/A')}\n\n"
            
            response += f"**AI Analysis:**\n"
            response += f"• Confidence: {item.ai_confidence}%\n"
            response += f"• Issue: {item.issue_description}\n"
            if item.ai_reasoning:
                response += f"• Reasoning: {item.ai_reasoning}\n"
            
            if str(item.status.value) != "pending":
                response += f"\n**Resolution:**\n"
                response += f"• Resolved: {item.resolved_at.strftime('%Y-%m-%d %H:%M')}\n"
                if item.resolution_notes:
                    response += f"• Notes: {item.resolution_notes}\n"
            
            return {
                "message": response,
                "action": "show_details",
                "data": {
                    "item_id": item_id,
                    "status": item.status.value,
                    "priority": item.priority.value,
                    "confidence": item.ai_confidence,
                    **source_details
                }
            }
            
        except Exception as e:
            logger.error(f"OrchestratorChat: Error showing details for {item_id}: {str(e)}")
            return self._error_response(f"Error retrieving details: {str(e)}")
    
    async def _handle_workload(
        self,
        db: AsyncSession,
        client_id: str
    ) -> Dict[str, Any]:
        """Show workload statistics"""
        
        # Count items by status
        pending_count = await db.execute(
            select(func.count(ReviewQueue.id))
            .where(
                ReviewQueue.client_id == UUID(client_id),
                cast(ReviewQueue.status, String) == 'PENDING'
            )
        )
        pending = pending_count.scalar()
        
        approved_today = await db.execute(
            select(func.count(ReviewQueue.id))
            .where(
                ReviewQueue.client_id == UUID(client_id),
                cast(ReviewQueue.status, String) == 'APPROVED',
                func.date(ReviewQueue.resolved_at) == datetime.utcnow().date()
            )
        )
        approved = approved_today.scalar()
        
        rejected_today = await db.execute(
            select(func.count(ReviewQueue.id))
            .where(
                ReviewQueue.client_id == UUID(client_id),
                cast(ReviewQueue.status, String) == 'REJECTED',
                func.date(ReviewQueue.resolved_at) == datetime.utcnow().date()
            )
        )
        rejected = rejected_today.scalar()
        
        response = f"📊 **Workload Overview**\n\n"
        response += f"**Pending:** {pending} items\n"
        response += f"**Today's activity:**\n"
        response += f"• ✅ Approved: {approved}\n"
        response += f"• ❌ Rejected: {rejected}\n"
        
        if pending == 0:
            response += f"\n🎉 All caught up! No pending items."
        elif pending <= 5:
            response += f"\n👍 Light workload today."
        else:
            response += f"\n⚠️ {pending} items need attention."
        
        return {
            "message": response,
            "action": "workload",
            "data": {
                "pending": pending,
                "approved_today": approved,
                "rejected_today": rejected
            }
        }
    
    async def _handle_general_query(
        self,
        db: AsyncSession,
        client_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Handle general queries using Claude"""
        
        # Build context from database
        context = await self._build_context(db, client_id)
        
        # Build conversation for Claude
        messages = []
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Last 6 messages for context
        
        # Add current query with context
        prompt = f"""Context from system:
{context}

User query: {user_message}

Provide a helpful, concise response based on the context."""
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            # Call Claude
            response_text = await self.call_claude(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            
            return {
                "message": response_text,
                "action": "general_query",
                "data": {}
            }
            
        except Exception as e:
            logger.error(f"OrchestratorChat: Error calling Claude: {str(e)}")
            return self._error_response("I'm having trouble processing that request. Please try again.")
    
    async def _build_context(self, db: AsyncSession, client_id: str) -> str:
        """Build context string from current system state"""
        
        # Get pending count
        pending_result = await db.execute(
            select(func.count(ReviewQueue.id))
            .where(
                ReviewQueue.client_id == UUID(client_id),
                cast(ReviewQueue.status, String) == 'PENDING'
            )
        )
        pending_count = pending_result.scalar()
        
        # Get recent items
        recent_result = await db.execute(
            select(ReviewQueue)
            .where(
                ReviewQueue.client_id == UUID(client_id),
                cast(ReviewQueue.status, String) == 'PENDING'
            )
            .order_by(desc(ReviewQueue.priority), ReviewQueue.created_at)
            .limit(3)
        )
        recent_items = recent_result.scalars().all()
        
        context = f"Current state:\n"
        context += f"- Pending review items: {pending_count}\n"
        
        if recent_items:
            context += f"\nRecent items:\n"
            for item in recent_items:
                context += f"- {item.id}: {item.issue_description} (confidence: {item.ai_confidence}%)\n"
        
        return context
    
    async def _get_source_details(
        self,
        db: AsyncSession,
        item: ReviewQueue
    ) -> Dict[str, Any]:
        """Get details about the source entity"""
        
        details = {}
        
        if item.source_type == "general_ledger":
            result = await db.execute(
                select(GeneralLedger).where(GeneralLedger.id == item.source_id)
            )
            entry = result.scalar_one_or_none()
            
            if entry:
                # Get vendor from vendor_invoice if linked
                vendor_name = "Unknown"
                if entry.source_type == "vendor_invoice":
                    invoice_result = await db.execute(
                        select(VendorInvoice).where(VendorInvoice.id == entry.source_id)
                    )
                    invoice = invoice_result.scalar_one_or_none()
                    if invoice:
                        vendor_result = await db.execute(
                            select(Vendor).where(Vendor.id == invoice.vendor_id)
                        )
                        vendor = vendor_result.scalar_one_or_none()
                        if vendor:
                            vendor_name = vendor.name
                
                # Calculate total from lines
                total = sum(line.debit_amount or 0 for line in entry.lines) if entry.lines else 0
                
                details = {
                    "amount": f"{total:.2f} NOK",
                    "vendor": vendor_name,
                    "date": entry.accounting_date.strftime('%Y-%m-%d') if entry.accounting_date else "N/A",
                    "description": entry.description or "N/A",
                    "voucher": f"{entry.voucher_series}-{entry.voucher_number}"
                }
        
        elif item.source_type == "vendor_invoice":
            result = await db.execute(
                select(VendorInvoice).where(VendorInvoice.id == item.source_id)
            )
            invoice = result.scalar_one_or_none()
            
            if invoice:
                vendor_result = await db.execute(
                    select(Vendor).where(Vendor.id == invoice.vendor_id)
                )
                vendor = vendor_result.scalar_one_or_none()
                
                details = {
                    "amount": f"{invoice.total_amount:.2f} NOK",
                    "vendor": vendor.name if vendor else "Unknown",
                    "date": invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else "N/A",
                    "invoice_number": invoice.invoice_number or "N/A"
                }
        
        return details
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "message": f"❌ {message}",
            "action": "error",
            "data": {"error": message}
        }
