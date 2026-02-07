#!/usr/bin/env python3
"""
Test script for chat booking functionality
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.services.chat.intent_classifier import IntentClassifier
from app.services.chat.context_manager import ContextManager


async def test_intent_classifier():
    """Test intent classification"""
    print("🧪 Testing Intent Classifier...")
    
    classifier = IntentClassifier()
    
    test_messages = [
        "Bokfør faktura INV-12345",
        "Vis meg fakturaer som venter",
        "Hva er status på alle fakturaer?",
        "help",
        "ja",
        "Korriger bokføring: bruk konto 6340"
    ]
    
    for msg in test_messages:
        result = await classifier.classify(msg)
        print(f"\n  Message: '{msg}'")
        print(f"  Intent: {result['intent']} (confidence: {result['confidence']})")
        if result.get('entities'):
            print(f"  Entities: {result['entities']}")
    
    print("\n✅ Intent classifier test complete")


def test_context_manager():
    """Test context management"""
    print("\n🧪 Testing Context Manager...")
    
    manager = ContextManager()
    
    # Create session
    session_id = "test-session-123"
    
    # Add messages
    manager.add_message(session_id, "user", "Bokfør faktura INV-12345")
    manager.add_message(session_id, "assistant", "Analyserer faktura...")
    
    # Update context
    manager.update_context(
        session_id,
        current_invoice_id="inv-uuid-123",
        current_invoice_number="INV-12345"
    )
    
    # Set pending confirmation
    manager.set_pending_confirmation(
        session_id,
        action="book_invoice",
        data={"invoice_id": "inv-uuid-123"},
        question="Bokfør nå?"
    )
    
    # Get context
    context = manager.get_context(session_id)
    
    print(f"\n  Session ID: {context['session_id']}")
    print(f"  Current invoice: {context['current_invoice_number']}")
    print(f"  Message count: {len(context['conversation_history'])}")
    print(f"  Pending confirmation: {context['pending_confirmation'] is not None}")
    
    # Get pending
    pending = manager.get_pending_confirmation(session_id)
    print(f"  Pending action: {pending['action']}")
    
    # Clear
    manager.clear_context(session_id)
    
    print("\n✅ Context manager test complete")


def test_imports():
    """Test all imports"""
    print("\n🧪 Testing Imports...")
    
    try:
        from app.services.chat import (
            ChatService,
            IntentClassifier,
            ContextManager,
            BookingActionHandler,
            StatusQueryHandler,
            ApprovalHandler,
            CorrectionHandler
        )
        print("  ✅ All chat service imports successful")
        
        from app.api.routes.chat_booking import router
        print("  ✅ Chat booking router imported")
        
        # Check routes
        routes = [r.path for r in router.routes]
        print(f"  ✅ {len(routes)} routes registered:")
        for route in routes:
            print(f"     - {route}")
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False
    
    print("\n✅ All imports test complete")
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("CHAT BOOKING TEST SUITE")
    print("=" * 60)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed, stopping")
        return
    
    # Test context manager
    test_context_manager()
    
    # Test intent classifier
    await test_intent_classifier()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start backend: cd backend && python -m uvicorn app.main:app --reload")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Open http://localhost:3000")
    print("4. Click 💬 button and test chat commands")


if __name__ == "__main__":
    asyncio.run(main())
