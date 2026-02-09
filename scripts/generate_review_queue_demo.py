#!/usr/bin/env python3
"""
Generate demo invoices for Review Queue testing
Creates 20 invoices with varying confidence levels
"""
import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.client import Client
from app.models.vendor import Vendor
from app.models.vendor_invoice import VendorInvoice
from app.services.review_queue_manager import process_invoice_for_review


# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://erp_user:erp_password@localhost:5432/ai_erp"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Demo vendors with different familiarity levels
DEMO_VENDORS = [
    # High familiarity (>20 invoices)
    {
        'name': 'PowerOffice AS',
        'org_number': '123456789',
        'invoice_count': 25,
        'typical_amount': 5000,
        'typical_accounts': ['6900', '2700', '2400']
    },
    {
        'name': 'Telenor Norge AS',
        'org_number': '987654321',
        'invoice_count': 30,
        'typical_amount': 3500,
        'typical_accounts': ['6900', '2700', '2400']
    },
    # Medium familiarity (5-10 invoices)
    {
        'name': 'Microsoft Norge AS',
        'org_number': '555666777',
        'invoice_count': 8,
        'typical_amount': 15000,
        'typical_accounts': ['6940', '2700', '2400']
    },
    {
        'name': 'Google Norway AS',
        'org_number': '444555666',
        'invoice_count': 6,
        'typical_amount': 8000,
        'typical_accounts': ['6900', '2700', '2400']
    },
    # Low familiarity (1-2 invoices)
    {
        'name': 'Kontorrekvisita AS',
        'org_number': '111222333',
        'invoice_count': 2,
        'typical_amount': 2500,
        'typical_accounts': ['6400', '2700', '2400']
    },
    {
        'name': 'Møbelhuset Bergen',
        'org_number': '999888777',
        'invoice_count': 1,
        'typical_amount': 25000,
        'typical_accounts': ['1230', '2700', '2400']
    },
    # New vendors (0 invoices)
    {
        'name': 'Nye Leverandør AS',
        'org_number': '777888999',
        'invoice_count': 0,
        'typical_amount': 12000,
        'typical_accounts': ['6900', '2700', '2400']
    },
    {
        'name': 'Ukjent Firma AS',
        'org_number': '666777888',
        'invoice_count': 0,
        'typical_amount': 150000,  # Large amount
        'typical_accounts': ['1230', '2700', '2400']
    }
]


async def create_vendor_with_history(
    db: AsyncSession,
    client_id: str,
    vendor_data: dict
) -> Vendor:
    """
    Create vendor and historical invoices (or find existing)
    """
    # Check if vendor already exists
    from app.models.vendor import Vendor
    existing_query = select(Vendor).where(
        and_(
            Vendor.client_id == client_id,
            Vendor.org_number == vendor_data['org_number']
        )
    )
    existing_result = await db.execute(existing_query)
    existing_vendor = existing_result.scalars().first()
    
    if existing_vendor:
        print(f"  Vendor already exists, using existing: {existing_vendor.name}")
        return existing_vendor
    
    # Generate unique vendor number
    max_vendor_query = select(func.max(Vendor.vendor_number)).where(
        Vendor.client_id == client_id
    )
    max_result = await db.execute(max_vendor_query)
    max_vendor_number = max_result.scalar()
    
    if max_vendor_number:
        try:
            next_number = int(max_vendor_number) + 1
        except:
            next_number = 1000
    else:
        next_number = 1
    
    vendor_number = str(next_number).zfill(4)
    
    # Create vendor
    vendor = Vendor(
        id=uuid4(),
        client_id=client_id,
        vendor_number=vendor_number,
        name=vendor_data['name'],
        org_number=vendor_data['org_number'],
        email=f"invoice@{vendor_data['name'].lower().replace(' ', '')}.no",
        account_number='2400',  # Standard accounts payable
        payment_terms='14',
        is_active=True
    )
    
    db.add(vendor)
    await db.flush()
    
    # Create historical invoices (already booked)
    for i in range(vendor_data['invoice_count']):
        days_ago = random.randint(30, 365)
        invoice_date = datetime.now().date() - timedelta(days=days_ago)
        
        amount_variation = random.uniform(0.8, 1.2)
        amount_excl_vat = Decimal(str(int(vendor_data['typical_amount'] * amount_variation)))
        vat_amount = amount_excl_vat * Decimal('0.25')
        total_amount = amount_excl_vat + vat_amount
        
        historical_invoice = VendorInvoice(
            id=uuid4(),
            client_id=client_id,
            vendor_id=vendor.id,
            invoice_number=f"HIST-{vendor_data['org_number']}-{i+1}",
            invoice_date=invoice_date,
            due_date=invoice_date + timedelta(days=14),
            amount_excl_vat=amount_excl_vat,
            vat_amount=vat_amount,
            total_amount=total_amount,
            currency='NOK',
            ai_processed=True,
            ai_confidence_score=random.randint(85, 95),
            review_status='auto_approved',
            general_ledger_id=None  # Not actually booked, just for history
        )
        
        db.add(historical_invoice)
    
    await db.commit()
    return vendor


async def generate_booking_suggestion(
    vendor_data: dict,
    amount_excl_vat: Decimal,
    vat_amount: Decimal,
    total_amount: Decimal,
    intentional_error: bool = False
) -> dict:
    """
    Generate AI booking suggestion (with optional intentional error for testing corrections)
    """
    accounts = vendor_data['typical_accounts'].copy()
    
    # Intentional error: use wrong account
    if intentional_error:
        wrong_accounts = ['6700', '6800', '6950']  # Different accounts
        accounts[0] = random.choice(wrong_accounts)
    
    lines = [
        {
            'account': accounts[0],
            'description': f'Kostnad - {vendor_data["name"]}',
            'debit': float(amount_excl_vat),
            'credit': 0,
            'vat_code': '3',
            'vat_amount': float(vat_amount)
        },
        {
            'account': accounts[1],  # 2700 = VAT payable
            'description': 'Utgående MVA',
            'debit': float(vat_amount),
            'credit': 0,
            'vat_code': None,
            'vat_amount': 0
        },
        {
            'account': accounts[2],  # 2400 = Accounts payable
            'description': f'Leverandørgjeld - {vendor_data["name"]}',
            'debit': 0,
            'credit': float(total_amount),
            'vat_code': None,
            'vat_amount': 0
        }
    ]
    
    return {
        'lines': lines,
        'confidence': None  # Will be calculated
    }


async def generate_demo_invoices(client_id: str):
    """
    Generate 20 demo invoices with varying confidence levels
    """
    async with AsyncSessionLocal() as db:
        print("🎯 Generating Review Queue Demo Data...")
        print(f"Client ID: {client_id}\n")
        
        # Create vendors with history
        vendors = []
        for vendor_data in DEMO_VENDORS:
            print(f"Creating vendor: {vendor_data['name']} (history: {vendor_data['invoice_count']} invoices)")
            vendor = await create_vendor_with_history(db, client_id, vendor_data)
            vendors.append((vendor, vendor_data))
        
        print(f"\n✅ Created {len(vendors)} vendors with historical data\n")
        
        # Generate 20 new test invoices
        print("Generating 20 test invoices...\n")
        
        results = {
            'auto_approved': 0,
            'needs_review': 0,
            'total': 0
        }
        
        for i in range(20):
            # Select vendor (weighted towards familiar vendors)
            vendor_weights = [v[1]['invoice_count'] + 1 for v in vendors]
            vendor, vendor_data = random.choices(vendors, weights=vendor_weights)[0]
            
            # Generate invoice data
            days_ago = random.randint(1, 30)
            invoice_date = datetime.now().date() - timedelta(days=days_ago)
            
            # Amount variation
            amount_variation = random.uniform(0.7, 1.5)
            amount_excl_vat = Decimal(str(int(vendor_data['typical_amount'] * amount_variation)))
            vat_amount = amount_excl_vat * Decimal('0.25')
            total_amount = amount_excl_vat + vat_amount
            
            # Intentional error for some invoices (20% chance)
            intentional_error = random.random() < 0.2
            
            # Create invoice
            invoice = VendorInvoice(
                id=uuid4(),
                client_id=client_id,
                vendor_id=vendor.id,
                invoice_number=f"TEST-{invoice_date.strftime('%Y%m%d')}-{i+1:03d}",
                invoice_date=invoice_date,
                due_date=invoice_date + timedelta(days=14),
                amount_excl_vat=amount_excl_vat,
                vat_amount=vat_amount,
                total_amount=total_amount,
                currency='NOK',
                ai_processed=False
            )
            
            db.add(invoice)
            await db.flush()
            
            # Generate booking suggestion
            booking_suggestion = await generate_booking_suggestion(
                vendor_data=vendor_data,
                amount_excl_vat=amount_excl_vat,
                vat_amount=vat_amount,
                total_amount=total_amount,
                intentional_error=intentional_error
            )
            
            # Process with confidence scoring
            result = await process_invoice_for_review(
                db=db,
                invoice_id=invoice.id,
                booking_suggestion=booking_suggestion
            )
            
            if result['success']:
                action = result['action']
                confidence = result['confidence']
                
                results['total'] += 1
                if action == 'auto_approved':
                    results['auto_approved'] += 1
                    status_icon = '✅'
                else:
                    results['needs_review'] += 1
                    status_icon = '⚠️'
                
                print(
                    f"{status_icon} Invoice {i+1:2d}: {vendor.name:30s} | "
                    f"{total_amount:10,.2f} NOK | "
                    f"Confidence: {confidence:3d}% | "
                    f"{action.upper()}"
                )
            else:
                print(f"❌ Invoice {i+1}: FAILED - {result.get('error')}")
        
        await db.commit()
        
        # Print summary
        print(f"\n{'='*80}")
        print("📊 DEMO DATA GENERATION COMPLETE")
        print(f"{'='*80}")
        print(f"Total invoices:      {results['total']}")
        print(f"Auto-approved:       {results['auto_approved']} ({results['auto_approved']/results['total']*100:.1f}%)")
        print(f"Needs review:        {results['needs_review']} ({results['needs_review']/results['total']*100:.1f}%)")
        print(f"\n✅ Review Queue is ready for testing!")
        print(f"\n🌐 Open: http://localhost:3000/review-queue")


async def main():
    """Main entry point"""
    # Get first client from database
    async with AsyncSessionLocal() as db:
        query = select(Client).limit(1)
        result = await db.execute(query)
        client = result.scalar_one_or_none()
        
        if not client:
            print("❌ No client found in database. Please create a client first.")
            return
        
        client_id = str(client.id)
    
    await generate_demo_invoices(client_id)


if __name__ == "__main__":
    asyncio.run(main())
