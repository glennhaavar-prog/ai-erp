#!/usr/bin/env python3
"""
Test Currency Exchange Rate APIs

Run this script to verify that the currency APIs are working correctly.
"""
import asyncio
import httpx
from datetime import date


async def test_norges_bank_api():
    """Test fetching from Norges Bank API"""
    print("\n📊 Testing Norges Bank API...")
    
    currencies = ["USD", "EUR", "SEK", "DKK"]
    
    for currency in currencies:
        url = f"https://data.norges-bank.no/api/data/EXR/B.{currency}.NOK.SP"
        params = {"format": "sdmx-json", "lastNObservations": 1}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Parse response
                dataset = data.get("data", {}).get("dataSets", [{}])[0]
                series = dataset.get("series", {})
                
                if series:
                    series_key = list(series.keys())[0]
                    observations = series[series_key].get("observations", {})
                    
                    if observations:
                        obs_key = list(observations.keys())[0]
                        rate_value = observations[obs_key][0]
                        
                        print(f"  ✅ {currency}/NOK: {rate_value}")
                    else:
                        print(f"  ❌ {currency}: No observations found")
                else:
                    print(f"  ❌ {currency}: No series data")
        
        except Exception as e:
            print(f"  ❌ {currency}: Error - {e}")


async def test_coingecko_api():
    """Test fetching from CoinGecko API"""
    print("\n₿ Testing CoinGecko API...")
    
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "nok"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            btc_nok = data.get("bitcoin", {}).get("nok")
            if btc_nok:
                print(f"  ✅ BTC/NOK: {btc_nok:,.2f}")
            else:
                print(f"  ❌ BTC: No data found")
    
    except Exception as e:
        print(f"  ❌ BTC: Error - {e}")


async def test_local_api():
    """Test local currency API endpoints"""
    print("\n🔧 Testing Local API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    endpoints = [
        ("/api/currencies/supported", "GET", None),
        ("/api/currencies/rates/refresh", "POST", None),
        ("/api/currencies/rates", "GET", None),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint, method, data in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                
                if method == "GET":
                    response = await client.get(url)
                elif method == "POST":
                    response = await client.post(url, json=data if data else {})
                
                response.raise_for_status()
                result = response.json()
                
                print(f"  ✅ {method} {endpoint}")
                
                # Show some details for specific endpoints
                if endpoint == "/api/currencies/rates" and "rates" in result:
                    print(f"      Found {len(result['rates'])} currency rates")
                elif endpoint == "/api/currencies/rates/refresh":
                    print(f"      Updated: {result.get('updated', 0)}/{result.get('total', 0)}")
            
            except httpx.HTTPStatusError as e:
                print(f"  ❌ {method} {endpoint}: HTTP {e.response.status_code}")
            except Exception as e:
                print(f"  ❌ {method} {endpoint}: {e}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Currency Exchange Rate API Tests")
    print("=" * 60)
    
    # Test external APIs
    await test_norges_bank_api()
    await test_coingecko_api()
    
    # Test local API (requires backend to be running)
    print("\nTo test local API endpoints, make sure the backend is running:")
    print("  cd backend && python -m uvicorn app.main:app --reload")
    
    try:
        await test_local_api()
    except Exception as e:
        print(f"\n⚠️  Local API not available. Start the backend first.")
        print(f"    Error: {e}")
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
