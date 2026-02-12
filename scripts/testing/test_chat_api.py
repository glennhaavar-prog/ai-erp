#!/usr/bin/env python3
"""
Test script for Chat API
Run this to verify the chat endpoint is working correctly
"""
import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:4000"

def test_chat_endpoint(command: str, description: str):
    """Test a chat command"""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={"message": command, "context": {"useRealData": False}},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Role: {data['role']}")
            print(f"Content:\n{data['content']}")
            if data.get('data'):
                print(f"Data: {json.dumps(data['data'], indent=2)}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health_endpoint():
    """Test health check"""
    print(f"\n{'='*60}")
    print(f"Test: Health Check")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/chat/health")
        if response.status_code == 200:
            print(f"✅ Health check passed!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print(f"\n🧪 Testing Chat API at {API_BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Test health check
    test_health_endpoint()
    
    # Test commands
    test_chat_endpoint("help", "Help command")
    test_chat_endpoint("show reviews", "Show reviews command")
    test_chat_endpoint("status", "Status command")
    test_chat_endpoint("approve abc12345", "Approve command")
    test_chat_endpoint("reject def45678 Wrong amount", "Reject command with reason")
    test_chat_endpoint("unknown command", "Unknown command handling")
    
    print(f"\n{'='*60}")
    print("✅ All tests completed!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
