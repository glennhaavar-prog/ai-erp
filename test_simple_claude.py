#!/usr/bin/env python3
"""Simple Claude API test to verify it works before testing Invoice Agent"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/.openclaw/workspace/ai-erp/backend/.env')

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

print("🧪 Testing Claude with a simple accounting question...")
print("="*60)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=500,
    messages=[{
        "role": "user",
        "content": """Given this Norwegian invoice:

Leverandør: Staples Norge AS
Fakturanummer: 2024-001234
Beløp eksl. MVA: 1.950 NOK
MVA 25%: 487,50 NOK
Totalt: 2.437,50 NOK
Beskrivelse: Kontorrekvisita

Suggest accounting entries using Norwegian chart of accounts (NS 4102):
- Account 6300 is for office supplies
- Account 2740 is for input VAT
- Account 2400 is for accounts payable

Return as JSON."""
    }]
)

print("✅ Claude Response:")
print("="*60)
print(response.content[0].text)
print("="*60)
print("\n✅ Claude API is working and responding!")
