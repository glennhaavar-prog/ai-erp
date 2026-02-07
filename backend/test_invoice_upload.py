#!/usr/bin/env python3
"""
Test script for Invoice Upload API
"""
import requests
import sys
from pathlib import Path
import json

# Configuration
API_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{API_URL}/api/invoices/upload/"

# Test client ID (should exist in database)
TEST_CLIENT_ID = "550e8400-e29b-41d4-a716-446655440000"  # Replace with actual client_id


def create_dummy_pdf():
    """Create a simple dummy PDF for testing"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import io
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # Add invoice-like content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, "FAKTURA / INVOICE")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Fra / From: Test Leverandør AS")
    c.drawString(100, 730, "Org.nr: 987654321")
    c.drawString(100, 710, "Adresse: Testveien 1, 0123 Oslo")
    
    c.drawString(100, 670, "Til / To: Kontali AS")
    c.drawString(100, 650, "Fakturanummer / Invoice Number: INV-2024-001")
    c.drawString(100, 630, "Fakturadato / Invoice Date: 2024-02-07")
    c.drawString(100, 610, "Forfallsdato / Due Date: 2024-03-07")
    
    c.drawString(100, 560, "Beskrivelse / Description:")
    c.drawString(120, 540, "Kontorrekvisita / Office supplies")
    c.drawString(120, 520, "Lisenser / Software licenses")
    
    c.drawString(100, 480, "Beløp eks. mva / Amount excl. VAT: NOK 8,000.00")
    c.drawString(100, 460, "Mva 25% / VAT 25%: NOK 2,000.00")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 430, "Totalt / Total: NOK 10,000.00")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, 100, "Vennligst betal innen forfallsdato / Please pay before due date")
    
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()


def test_upload_with_dummy_pdf():
    """Test upload with generated dummy PDF"""
    print("🧪 Testing Invoice Upload API")
    print("=" * 60)
    
    # Create dummy PDF
    print("📄 Creating dummy PDF...")
    pdf_content = create_dummy_pdf()
    print(f"✅ Created PDF ({len(pdf_content)} bytes)")
    
    # Prepare multipart form data
    files = {
        'file': ('test_invoice.pdf', pdf_content, 'application/pdf')
    }
    data = {
        'client_id': TEST_CLIENT_ID
    }
    
    print(f"\n📤 Uploading to {UPLOAD_ENDPOINT}")
    print(f"   Client ID: {TEST_CLIENT_ID}")
    
    try:
        response = requests.post(
            UPLOAD_ENDPOINT,
            files=files,
            data=data,
            timeout=60  # OCR + AI can take time
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Upload Successful!")
            print("=" * 60)
            print(json.dumps(result, indent=2))
            print("=" * 60)
            
            # Summary
            print("\n📊 Summary:")
            print(f"   Invoice ID: {result.get('invoice_id')}")
            print(f"   Document ID: {result.get('document_id')}")
            print(f"   Review Queue ID: {result.get('review_queue_id')}")
            print(f"   S3 URL: {result.get('s3_url')}")
            print(f"   Confidence: {result.get('confidence_score')}%")
            print(f"   Status: {result.get('status')}")
            
            if result.get('invoice_details'):
                inv = result['invoice_details']
                print(f"\n   Invoice Number: {inv.get('invoice_number')}")
                print(f"   Amount: {inv.get('total_amount')} {inv.get('currency')}")
                print(f"   Date: {inv.get('invoice_date')}")
            
            return True
        else:
            print(f"\n❌ Upload Failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error!")
        print("   Is the server running? (python -m app.main)")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_upload_with_file(file_path: str):
    """Test upload with actual PDF file"""
    print("🧪 Testing Invoice Upload API with file")
    print("=" * 60)
    
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    if not pdf_path.suffix.lower() == '.pdf':
        print(f"❌ File must be a PDF: {file_path}")
        return False
    
    print(f"📄 Using PDF: {pdf_path.name}")
    
    with open(pdf_path, 'rb') as f:
        files = {
            'file': (pdf_path.name, f, 'application/pdf')
        }
        data = {
            'client_id': TEST_CLIENT_ID
        }
        
        print(f"\n📤 Uploading to {UPLOAD_ENDPOINT}")
        
        try:
            response = requests.post(
                UPLOAD_ENDPOINT,
                files=files,
                data=data,
                timeout=60
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ Upload Successful!")
                print("=" * 60)
                print(json.dumps(result, indent=2))
                return True
            else:
                print(f"\n❌ Upload Failed!")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return False


def test_list_invoices():
    """Test listing invoices"""
    print("\n🧪 Testing Invoice List API")
    print("=" * 60)
    
    url = f"{API_URL}/api/invoices/?client_id={TEST_CLIENT_ID}"
    print(f"📤 GET {url}")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            invoices = response.json()
            print(f"\n✅ Found {len(invoices)} invoices")
            
            for inv in invoices[:5]:  # Show first 5
                print(f"\n   Invoice: {inv['invoice_number']}")
                print(f"   Amount: {inv['total_amount']} {inv['currency']}")
                print(f"   Vendor: {inv['vendor_name']}")
                print(f"   Status: {inv['review_status']}")
                print(f"   Confidence: {inv.get('ai_confidence_score')}%")
            
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    # Check if reportlab is installed
    try:
        import reportlab
    except ImportError:
        print("⚠️  reportlab not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        print("✅ reportlab installed")
    
    # Check if file path provided
    if len(sys.argv) > 1:
        # Test with provided file
        success = test_upload_with_file(sys.argv[1])
    else:
        # Test with dummy PDF
        success = test_upload_with_dummy_pdf()
    
    # Also test listing
    test_list_invoices()
    
    sys.exit(0 if success else 1)
