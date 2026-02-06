#!/usr/bin/env python3
"""Test Invoice Agent with mock OCR data"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.agents.invoice_agent import InvoiceAgent
from dotenv import load_dotenv

# Load env
load_dotenv('/home/ubuntu/.openclaw/workspace/ai-erp/backend/.env')

# Mock OCR text from a Norwegian invoice
MOCK_INVOICE_TEXT = """
FAKTURA

Leverandør: Staples Norge AS
Org.nr: 987 654 321
Postboks 123
0566 Oslo

Kunde: Kontali AS
Org.nr: 123 456 789

Fakturanummer: 2024-001234
Fakturadato: 05.02.2024
Forfallsdato: 05.03.2024

Varebeskrivelse                Antall    Pris      Sum
------------------------------------------------------
Kontorrekvisita - A4 papir         10    120,00   1.200,00
Skriveredskap                       5    150,00     750,00
                                                  ---------
Subtotal                                          1.950,00
MVA 25%                                             487,50
                                                  ---------
Totalt å betale                                   2.437,50 NOK

Vennligst betal til:
Bankkonto: 1234.56.78901
KID: 12345678901234
"""

async def test_invoice_agent():
    print("="*60)
    print("🧪 TESTING INVOICE AGENT WITH MOCK DATA")
    print("="*60)
    
    agent = InvoiceAgent()
    
    print("\n📄 Mock Invoice Text:")
    print("-" * 60)
    print(MOCK_INVOICE_TEXT[:200] + "...")
    print("-" * 60)
    
    print("\n🤖 Analyzing invoice with Claude AI...")
    
    try:
        # Use a dummy UUID for testing
        import uuid
        test_client_id = uuid.uuid4()
        
        result = await agent.analyze_invoice(
            client_id=test_client_id,
            ocr_text=MOCK_INVOICE_TEXT,
            vendor_history=None,
            learned_patterns=None
        )
        
        print("\n✅ ANALYSIS COMPLETE!")
        print("="*60)
        
        print("\n🔍 Raw result:")
        print(result)
        print("\n" + "-"*60)
        
        print("\n📊 Confidence Score:", result.get('confidence_score', 0))
        
        print("\n🏢 Vendor Information:")
        print(f"  Name: {result['vendor']['name']}")
        print(f"  Org Number: {result['vendor']['org_number']}")
        
        print("\n💰 Invoice Details:")
        print(f"  Invoice Number: {result['invoice_number']}")
        print(f"  Date: {result['invoice_date']}")
        print(f"  Due Date: {result['due_date']}")
        print(f"  Amount (excl VAT): {result['amount_excl_vat']} {result['currency']}")
        print(f"  VAT: {result['vat_amount']} {result['currency']}")
        print(f"  Total: {result['total_amount']} {result['currency']}")
        
        print("\n📝 Suggested Booking:")
        for line in result['suggested_booking']:
            debit = f"{line['debit']:.2f}" if line.get('debit') else "-"
            credit = f"{line['credit']:.2f}" if line.get('credit') else "-"
            print(f"  Account {line['account']}: Debit: {debit}, Credit: {credit}")
            print(f"    Description: {line['description']}")
        
        print("\n🧠 AI Reasoning:")
        print(f"  {result['reasoning'][:150]}...")
        
        print("\n" + "="*60)
        
        if result['confidence_score'] >= 85:
            print("✅ CONFIDENCE ≥ 85% - Would AUTO-APPROVE")
        else:
            print("⚠️  CONFIDENCE < 85% - Would send to REVIEW QUEUE")
        
        print("="*60)
        
        return result
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_invoice_agent())
    
    if result:
        print("\n✅ Invoice Agent is WORKING!")
        sys.exit(0)
    else:
        print("\n❌ Invoice Agent test FAILED")
        sys.exit(1)
