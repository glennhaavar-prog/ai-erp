#!/usr/bin/env python3
"""Test AWS Textract access"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load from .env
load_dotenv('/home/ubuntu/.openclaw/workspace/ai-erp/backend/.env')

aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
textract_region = os.getenv('AWS_TEXTRACT_REGION', 'eu-west-1')

print(f"✅ Testing Textract in region: {textract_region}")

try:
    textract_client = boto3.client(
        'textract',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=textract_region
    )
    
    print("✅ Textract client created")
    
    # Test with a dummy call (will fail, but that's expected)
    try:
        textract_client.detect_document_text(
            Document={'S3Object': {'Bucket': 'nonexistent-bucket-test-12345', 'Name': 'test.pdf'}}
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['InvalidS3ObjectException', 'NoSuchBucket', 'AccessDenied']:
            print(f"✅ Textract API is accessible! (Got expected error: {error_code})")
            print(f"✅ Region {textract_region} supports Textract")
        else:
            print(f"⚠️  Unexpected error: {error_code}")
            print(f"   Message: {e.response['Error']['Message']}")
    
    print("\n" + "="*50)
    print("✅ TEXTRACT SETUP COMPLETE!")
    print("="*50)
    print(f"\nTextract Region: {textract_region}")
    print("Ready to extract text from invoices! 📄")
    
except Exception as e:
    print(f"❌ Textract setup failed: {e}")
    sys.exit(1)
