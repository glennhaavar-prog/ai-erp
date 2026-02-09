#!/usr/bin/env python3
"""
Healthcheck script for Kontali Backend

Usage:
  python3 healthcheck.py [--url http://localhost:8000] [--timeout 5]

Exit codes:
  0 - Healthy
  1 - Unhealthy (HTTP error or timeout)
  2 - Invalid arguments
"""

import sys
import argparse
import requests
from typing import Tuple


def check_health(url: str, timeout: int) -> Tuple[bool, str]:
    """
    Check backend health endpoint
    
    Returns:
        (is_healthy, message)
    """
    try:
        response = requests.get(
            f"{url}/health",
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                return True, f"✓ Backend healthy: {data.get('app')} v{data.get('version')}"
            else:
                return False, f"✗ Backend unhealthy: {data}"
        else:
            return False, f"✗ HTTP {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return False, f"✗ Timeout after {timeout}s"
    except requests.exceptions.ConnectionError:
        return False, f"✗ Connection refused"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Kontali Backend Healthcheck")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Request timeout in seconds (default: 5)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (only exit code)"
    )
    
    args = parser.parse_args()
    
    is_healthy, message = check_health(args.url, args.timeout)
    
    if not args.quiet:
        print(message)
    
    sys.exit(0 if is_healthy else 1)


if __name__ == "__main__":
    main()
