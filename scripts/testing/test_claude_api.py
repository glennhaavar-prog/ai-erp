#!/usr/bin/env python3
"""Quick test to verify Claude API key works"""

import os
import sys
from anthropic import Anthropic

# Load from .env
from dotenv import load_dotenv
load_dotenv('/home/ubuntu/.openclaw/workspace/ai-erp/backend/.env')

api_key = os.getenv('ANTHROPIC_API_KEY')

if not api_key:
    print("❌ ANTHROPIC_API_KEY not found in .env")
    sys.exit(1)

print("✅ API Key found (ending in: ...{})".format(api_key[-10:]))

try:
    client = Anthropic(api_key=api_key)
    
    print("🔄 Testing API call...")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Say 'API test successful!' if you can read this."}
        ]
    )
    
    result = response.content[0].text
    print(f"✅ API Response: {result}")
    print("✅ Claude API key is WORKING!")
    
except Exception as e:
    print(f"❌ API call failed: {e}")
    sys.exit(1)
