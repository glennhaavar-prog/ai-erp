#!/usr/bin/env python3
"""Complete invoice processing: PDF → Textract → Invoice Agent → Result"""

import asyncio
import sys
import os
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from app.agents.invoice_agent import InvoiceAgent

# Load env
load_dotenv('/home/ubuntu/.openclaw/workspace/ai-erp/backend/.env')

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using AWS Textract"""
    
    aws_access_key = os.getenv('AWS_ACCESS_KEY')
    aws_secret_key = os.getenv('AWS_SECRET_KEY')
    aws_region = os.getenv('AWS_REGION', 'eu-north-1')
    textract_region = os.getenv('AWS_TEXTRACT_REGION', 'eu-west-1')
    s3_bucket = os.getenv('S3_BUCKET_DOCUMENTS', 'kontali-erp-documents')
    
    # Create AWS clients
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
        region_name=textract_region
    )
    
    # Upload PDF to S3
    print(f"📤 Uploading PDF to S3...")
    pdf_filename = Path(pdf_path).name
    s3_key = f"temp/{pdf_filename}"
    
    try:
        s3_client.upload_file(pdf_path, s3_bucket, s3_key)
        print(f"✅ Uploaded to s3://{s3_bucket}/{s3_key}")
    except ClientError as e:
        print(f"❌ Failed to upload to S3: {e}")
        raise
    
    # Extract text with Textract
    print(f"🔍 Extracting text with AWS Textract...")
    
    try:
        response = textract_client.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': s3_bucket,
                    'Name': s3_key
                }
            }
        )
        
        # Extract all text blocks
        text_blocks = []
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
        
        extracted_text = '\n'.join(text_blocks)
        print(f"✅ Extracted {len(text_blocks)} lines of text")
        
        # Clean up S3
        print(f"🗑️  Cleaning up S3...")
        s3_client.delete_object(Bucket=s3_bucket, Key=s3_key)
        
        return extracted_text
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ Textract failed with error: {error_code}")
        print(f"   Message: {e.response['Error']['Message']}")
        raise

async def process_invoice(pdf_path: str):
    """Complete invoice processing pipeline"""
    
    print("="*70)
    print(f"🧾 PROCESSING INVOICE: {Path(pdf_path).name}")
    print("="*70)
    
    # Step 1: Extract text with Textract
    print("\n📄 STEP 1: OCR Extraction")
    print("-"*70)
    
    try:
        ocr_text = extract_text_from_pdf(pdf_path)
        
        print("\n📋 Extracted Text Preview (first 500 chars):")
        print("-"*70)
        print(ocr_text[:500])
        print("...")
        print("-"*70)
        
    except Exception as e:
        print(f"\n❌ OCR Extraction failed: {e}")
        return None
    
    # Step 2: Analyze with Invoice Agent
    print("\n🤖 STEP 2: AI Analysis with Claude")
    print("-"*70)
    
    try:
        agent = InvoiceAgent()
        
        # Use dummy client ID for testing
        import uuid
        test_client_id = uuid.uuid4()
        
        result = await agent.analyze_invoice(
            client_id=test_client_id,
            ocr_text=ocr_text,
            vendor_history=None,
            learned_patterns=None
        )
        
        # Check if analysis failed
        if 'error' in result:
            print(f"❌ Analysis failed: {result.get('error')}")
            print(f"   Reason: {result.get('reasoning')}")
            return None
        
        print("✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ AI Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Step 3: Display results
    print("\n📊 STEP 3: Results")
    print("="*70)
    
    print(f"\n🏢 Vendor: {result.get('vendor', {}).get('name', 'Unknown')}")
    print(f"📄 Invoice #: {result.get('invoice_number', 'N/A')}")
    print(f"📅 Date: {result.get('invoice_date', 'N/A')}")
    print(f"💰 Amount: {result.get('total_amount', 0)} {result.get('currency', 'NOK')}")
    print(f"📈 Confidence: {result.get('confidence_score', 0)}%")
    
    print("\n📝 Suggested Booking:")
    print("-"*70)
    for line in result.get('suggested_booking', []):
        debit = f"{line.get('debit', 0):>10.2f}" if line.get('debit') else " "*10
        credit = f"{line.get('credit', 0):>10.2f}" if line.get('credit') else " "*10
        print(f"  {line['account']:>4} | Debit: {debit} | Credit: {credit} | {line['description']}")
    
    print("\n🧠 AI Reasoning:")
    print("-"*70)
    print(f"  {result.get('reasoning', 'N/A')[:200]}...")
    
    print("\n" + "="*70)
    
    confidence = result.get('confidence_score', 0)
    if confidence >= 85:
        print("✅ CONFIDENCE ≥ 85% → Would AUTO-APPROVE")
    else:
        print("⚠️  CONFIDENCE < 85% → Would send to REVIEW QUEUE")
    
    print("="*70)
    
    return result

async def main():
    """Process invoice from command line"""
    
    if len(sys.argv) < 2:
        print("Usage: python process_invoice_pdf.py <path-to-pdf>")
        print("\nAvailable test invoices:")
        test_dir = Path(__file__).parent / 'test-invoices'
        for pdf in sorted(test_dir.glob('*.pdf')):
            print(f"  - {pdf.name}")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    result = await process_invoice(pdf_path)
    
    if result:
        print("\n✅ Invoice processing COMPLETE!")
        sys.exit(0)
    else:
        print("\n❌ Invoice processing FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
