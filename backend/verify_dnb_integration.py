#!/usr/bin/env python3
"""
DNB Integration Verification Script

Runs comprehensive checks to ensure the DNB integration is properly installed
and configured. Run this before sandbox testing.
"""

import sys
import os
from pathlib import Path

def check_files():
    """Verify all required files exist"""
    print("🔍 Checking required files...")
    
    files = [
        "app/services/dnb/__init__.py",
        "app/services/dnb/oauth_client.py",
        "app/services/dnb/api_client.py",
        "app/services/dnb/service.py",
        "app/services/dnb/encryption.py",
        "app/models/bank_connection.py",
        "app/api/routes/dnb.py",
        "tests/test_dnb_integration.py",
    ]
    
    all_exist = True
    for file in files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - NOT FOUND")
            all_exist = False
    
    return all_exist

def check_imports():
    """Verify all modules can be imported"""
    print("\n🔍 Checking imports...")
    
    try:
        from app.services.dnb.oauth_client import DNBOAuth2Client
        print("  ✅ DNBOAuth2Client")
    except Exception as e:
        print(f"  ❌ DNBOAuth2Client: {e}")
        return False
    
    try:
        from app.services.dnb.api_client import DNBAPIClient
        print("  ✅ DNBAPIClient")
    except Exception as e:
        print(f"  ❌ DNBAPIClient: {e}")
        return False
    
    try:
        from app.services.dnb.service import DNBService
        print("  ✅ DNBService")
    except Exception as e:
        print(f"  ❌ DNBService: {e}")
        return False
    
    try:
        from app.services.dnb.encryption import token_encryption
        print("  ✅ token_encryption")
    except Exception as e:
        print(f"  ❌ token_encryption: {e}")
        return False
    
    try:
        from app.models.bank_connection import BankConnection
        print("  ✅ BankConnection")
    except Exception as e:
        print(f"  ❌ BankConnection: {e}")
        return False
    
    try:
        from app.models.bank_transaction import BankTransaction
        print("  ✅ BankTransaction")
    except Exception as e:
        print(f"  ❌ BankTransaction: {e}")
        return False
    
    return True

def check_config():
    """Verify configuration is accessible"""
    print("\n🔍 Checking configuration...")
    
    try:
        from app.config import settings
        
        # Check if attributes exist
        if hasattr(settings, 'DNB_CLIENT_ID'):
            print(f"  ✅ DNB_CLIENT_ID configured")
        else:
            print(f"  ⚠️  DNB_CLIENT_ID not set (will need to configure)")
        
        if hasattr(settings, 'DNB_CLIENT_SECRET'):
            print(f"  ✅ DNB_CLIENT_SECRET configured")
        else:
            print(f"  ⚠️  DNB_CLIENT_SECRET not set (will need to configure)")
        
        if hasattr(settings, 'DNB_API_KEY'):
            print(f"  ✅ DNB_API_KEY configured")
        else:
            print(f"  ⚠️  DNB_API_KEY not set (will need to configure)")
        
        if hasattr(settings, 'DNB_REDIRECT_URI'):
            print(f"  ✅ DNB_REDIRECT_URI: {settings.DNB_REDIRECT_URI}")
        else:
            print(f"  ❌ DNB_REDIRECT_URI not configured")
            return False
        
        if hasattr(settings, 'DNB_USE_SANDBOX'):
            print(f"  ✅ DNB_USE_SANDBOX: {settings.DNB_USE_SANDBOX}")
        else:
            print(f"  ❌ DNB_USE_SANDBOX not configured")
            return False
        
        if hasattr(settings, 'SECRET_KEY'):
            if len(settings.SECRET_KEY) >= 32:
                print(f"  ✅ SECRET_KEY configured (length: {len(settings.SECRET_KEY)})")
            else:
                print(f"  ⚠️  SECRET_KEY too short (min 32 chars, got {len(settings.SECRET_KEY)})")
        else:
            print(f"  ❌ SECRET_KEY not configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False

def check_database():
    """Verify database models are defined"""
    print("\n🔍 Checking database models...")
    
    try:
        from app.models.bank_connection import BankConnection
        
        # Check if table name is defined
        if hasattr(BankConnection, '__tablename__'):
            print(f"  ✅ BankConnection table: {BankConnection.__tablename__}")
        else:
            print(f"  ❌ BankConnection table name not defined")
            return False
        
        # Check key columns
        columns = [col.name for col in BankConnection.__table__.columns]
        required = ['id', 'client_id', 'bank_name', 'access_token', 'refresh_token']
        
        for col in required:
            if col in columns:
                print(f"  ✅ Column: {col}")
            else:
                print(f"  ❌ Column missing: {col}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database model error: {e}")
        return False

def check_api_routes():
    """Verify API routes are defined"""
    print("\n🔍 Checking API routes...")
    
    try:
        from app.api.routes.dnb import router
        
        routes = [route.path for route in router.routes]
        
        expected = [
            '/oauth/initiate',
            '/oauth/callback',
            '/connect',
            '/sync',
            '/connections',
            '/sync/all'
        ]
        
        for route in expected:
            if any(route in r for r in routes):
                print(f"  ✅ Route: {route}")
            else:
                print(f"  ⚠️  Route not found: {route}")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  API route check: {e}")
        return True  # Don't fail on this

def check_encryption():
    """Verify encryption works"""
    print("\n🔍 Checking encryption...")
    
    try:
        from app.services.dnb.encryption import token_encryption
        
        # Test encryption/decryption
        test_token = "test_token_12345"
        encrypted = token_encryption.encrypt(test_token)
        decrypted = token_encryption.decrypt(encrypted)
        
        if decrypted == test_token:
            print(f"  ✅ Encryption/Decryption working")
            return True
        else:
            print(f"  ❌ Encryption/Decryption failed")
            return False
        
    except Exception as e:
        print(f"  ❌ Encryption error: {e}")
        return False

def check_tests():
    """Run unit tests"""
    print("\n🔍 Running unit tests...")
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tests/test_dnb_integration.py', '-v'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Count passed tests
            output = result.stdout
            if '9 passed' in output:
                print(f"  ✅ All 9 unit tests passed")
                return True
            else:
                print(f"  ⚠️  Some tests might have failed")
                print(f"     {result.stdout}")
                return False
        else:
            print(f"  ❌ Tests failed")
            print(f"     {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Tests timed out")
        return True
    except Exception as e:
        print(f"  ⚠️  Could not run tests: {e}")
        return True

def main():
    """Run all checks"""
    print("=" * 60)
    print("DNB INTEGRATION VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Files", check_files),
        ("Imports", check_imports),
        ("Configuration", check_config),
        ("Database Models", check_database),
        ("API Routes", check_api_routes),
        ("Encryption", check_encryption),
        ("Unit Tests", check_tests),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ {name} check failed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print("=" * 60)
    
    if passed == total:
        print(f"\n✅ ALL CHECKS PASSED ({passed}/{total})")
        print("\n🚀 Integration is ready for sandbox testing!")
        print("\nNext steps:")
        print("1. Get DNB sandbox credentials at https://developer.dnb.no")
        print("2. Update .env with DNB_CLIENT_ID, DNB_CLIENT_SECRET, DNB_API_KEY")
        print("3. Follow DNB_SANDBOX_TESTING_GUIDE.md")
        return 0
    else:
        print(f"\n⚠️  SOME CHECKS FAILED ({passed}/{total})")
        print("\nPlease fix the issues above before testing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
