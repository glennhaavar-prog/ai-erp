#!/usr/bin/env python3
"""Test AWS credentials and setup S3 bucket"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load from .env
load_dotenv('/home/ubuntu/.openclaw/workspace/ai-erp/backend/.env')

aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
aws_region = os.getenv('AWS_REGION', 'eu-north-1')
bucket_name = os.getenv('S3_BUCKET_DOCUMENTS', 'kontali-erp-documents')

if not aws_access_key or not aws_secret_key:
    print("❌ AWS credentials not found in .env")
    sys.exit(1)

print(f"✅ AWS Access Key found (ending in: ...{aws_access_key[-4:]})")
print(f"✅ AWS Region: {aws_region}")
print(f"✅ S3 Bucket name: {bucket_name}")

# Create AWS clients
try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    
    textract_client = boto3.client(
        'textract',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    
    print("✅ AWS clients created")
    
except Exception as e:
    print(f"❌ Failed to create AWS clients: {e}")
    sys.exit(1)

# Test credentials with S3
print("\n🔄 Testing AWS credentials with S3...")
try:
    s3_client.list_buckets()
    print("✅ AWS credentials are VALID!")
except ClientError as e:
    print(f"❌ AWS credentials test failed: {e}")
    sys.exit(1)

# Check if bucket exists
print(f"\n🔄 Checking if S3 bucket '{bucket_name}' exists...")
try:
    s3_client.head_bucket(Bucket=bucket_name)
    print(f"✅ Bucket '{bucket_name}' already exists!")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        print(f"⚠️  Bucket '{bucket_name}' does not exist. Creating it...")
        try:
            # Create bucket with proper location constraint
            if aws_region == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': aws_region}
                )
            
            # Enable versioning
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Block public access
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            
            print(f"✅ Bucket '{bucket_name}' created successfully!")
            print("✅ Versioning enabled")
            print("✅ Public access blocked")
            
        except ClientError as create_error:
            print(f"❌ Failed to create bucket: {create_error}")
            sys.exit(1)
    else:
        print(f"❌ Error checking bucket: {e}")
        sys.exit(1)

# Test Textract access
print("\n🔄 Testing AWS Textract access...")
try:
    # This will fail if we don't have Textract permissions
    # But that's okay - we just want to see if we can call the service
    textract_client.detect_document_text(
        Document={'S3Object': {'Bucket': 'test', 'Name': 'test'}}
    )
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'InvalidS3ObjectException' or error_code == 'NoSuchBucket':
        # Expected - we're just testing permissions
        print("✅ AWS Textract is accessible (permissions OK)")
    else:
        print(f"⚠️  Textract test returned: {error_code}")
        print("   This might be a permissions issue. Check IAM policy.")
except Exception as e:
    print(f"❌ Textract test failed: {e}")

print("\n" + "="*50)
print("✅ AWS SETUP COMPLETE!")
print("="*50)
print(f"\nS3 Bucket: {bucket_name}")
print(f"Region: {aws_region}")
print("\nReady to process invoices! 🚀")
