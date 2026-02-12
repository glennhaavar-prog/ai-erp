#!/usr/bin/env python3
"""
Simple Currency Rate Update Script (using API)

This script calls the API endpoint to update rates.
Use this for cron jobs.

Add to crontab:
# Update currency rates daily at 9:00 AM
0 9 * * * cd /path/to/backend && python scripts/update_currency_rates_simple.py
"""
import httpx
import sys
from datetime import datetime

API_URL = "http://localhost:8000/api/currencies/rates/refresh"

def update_rates():
    """Call API to update rates"""
    print(f"[{datetime.now()}] Calling currency rate update API...")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(API_URL)
            response.raise_for_status()
            data = response.json()
            
            print(f"[{datetime.now()}] API Response:")
            print(f"  Success: {data.get('success')}")
            print(f"  Updated: {data.get('updated')}/{data.get('total')}")
            
            for currency, success in data.get('results', {}).items():
                status = "✅" if success else "❌"
                print(f"  {status} {currency}")
            
            print(f"[{datetime.now()}] Currency rate update complete!")
            return data.get('success', False)
    
    except httpx.HTTPError as e:
        print(f"[{datetime.now()}] HTTP ERROR: {e}")
        return False
    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")
        return False

def main():
    """Main entry point"""
    success = update_rates()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
