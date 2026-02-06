#!/usr/bin/env python3
"""Create S3 bucket in eu-west-1 for Textract"""

import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/.openclaw/workspace/ai-erp/backend/.env')

aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
textract_region = 'eu-west-1'
new_bucket_name = 'kontali-erp-documents-eu-west-1'

s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=textract_region
)

print(f"🔧 Creating S3 bucket in {textract_region}...")

try:
    # Check if bucket exists
    try:
        s3_client.head_bucket(Bucket=new_bucket_name)
        print(f"✅ Bucket '{new_bucket_name}' already exists!")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            # Create bucket
            s3_client.create_bucket(
                Bucket=new_bucket_name,
                CreateBucketConfiguration={'LocationConstraint': textract_region}
            )
            
            # Enable versioning
            s3_client.put_bucket_versioning(
                Bucket=new_bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Block public access
            s3_client.put_public_access_block(
                Bucket=new_bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            
            print(f"✅ Bucket '{new_bucket_name}' created successfully!")
            print("✅ Versioning enabled")
            print("✅ Public access blocked")
        else:
            raise
    
    print(f"\n✅ DONE! Update .env with:")
    print(f"   S3_BUCKET_DOCUMENTS=\"{new_bucket_name}\"")

except Exception as e:
    print(f"❌ Failed: {e}")
    raise
