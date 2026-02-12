"""
Contact Import Service - Bulk CSV/Excel Import for Suppliers and Customers

Handles parsing, validation, and bulk creation of contact records.
"""
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

from app.models.supplier import Supplier
from app.models.customer import Customer


async def generate_next_supplier_number(db: AsyncSession, client_id) -> str:
    """Generate next sequential supplier number"""
    result = await db.execute(
        select(Supplier)
        .where(Supplier.client_id == client_id)
        .order_by(Supplier.supplier_number.desc())
        .limit(1)
    )
    last_supplier = result.scalar_one_or_none()
    
    if last_supplier and last_supplier.supplier_number.isdigit():
        next_number = int(last_supplier.supplier_number) + 1
    else:
        next_number = 1
    
    return str(next_number).zfill(5)


async def generate_next_customer_number(db: AsyncSession, client_id) -> str:
    """Generate next sequential customer number"""
    result = await db.execute(
        select(Customer)
        .where(Customer.client_id == client_id)
        .order_by(Customer.customer_number.desc())
        .limit(1)
    )
    last_customer = result.scalar_one_or_none()
    
    if last_customer and last_customer.customer_number.isdigit():
        next_number = int(last_customer.customer_number) + 1
    else:
        next_number = 1
    
    return str(next_number).zfill(5)


class ContactImportResult:
    """Result of a bulk import operation"""
    
    def __init__(self):
        self.created = 0
        self.skipped = 0
        self.errors: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "created": self.created,
            "skipped": self.skipped,
            "error_count": len(self.errors),
            "errors": self.errors
        }


def parse_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    Parse uploaded CSV or Excel file into DataFrame
    
    Args:
        file_content: Raw file bytes
        filename: Original filename (used to detect format)
    
    Returns:
        pandas DataFrame with contact data
    
    Raises:
        ValueError: If file format is invalid or parsing fails
    """
    try:
        file_obj = BytesIO(file_content)
        
        if filename.endswith('.csv'):
            df = pd.read_csv(file_obj, encoding='utf-8')
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_obj)
        else:
            raise ValueError(f"Unsupported file format: {filename}")
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Replace NaN with None
        df = df.where(pd.notnull(df), None)
        
        return df
    
    except Exception as e:
        raise ValueError(f"Failed to parse file: {str(e)}")


def validate_org_number(org_number: Optional[str]) -> Optional[str]:
    """
    Validate and clean Norwegian organization number
    
    Returns:
        Cleaned org_number (digits only) or None if invalid
    """
    if not org_number:
        return None
    
    # Remove spaces and non-digits
    cleaned = re.sub(r'\D', '', str(org_number))
    
    # Must be 9 digits
    if len(cleaned) != 9:
        return None
    
    return cleaned


def validate_phone(phone: Optional[str]) -> Optional[str]:
    """Clean and validate phone number"""
    if not phone:
        return None
    
    # Remove spaces and non-digits
    cleaned = re.sub(r'\D', '', str(phone))
    
    return cleaned if cleaned else None


def validate_email(email: Optional[str]) -> Optional[str]:
    """Basic email validation"""
    if not email:
        return None
    
    email = str(email).strip()
    
    # Basic email pattern
    if '@' in email and '.' in email.split('@')[1]:
        return email
    
    return None


async def import_suppliers(
    db: AsyncSession,
    df: pd.DataFrame,
    client_id
) -> ContactImportResult:
    """
    Bulk import suppliers from DataFrame
    
    Expected columns:
    - navn (required)
    - org_nummer (required)
    - epost
    - telefon
    - adresse
    - postnummer
    - poststed
    - land
    - kontonummer
    - betalingsbetingelser (e.g., "30 dager")
    - leverandor_type (goods/services)
    """
    result = ContactImportResult()
    
    # Validate required columns
    required_cols = ['navn', 'org_nummer']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        result.errors.append({
            "row": 0,
            "error": f"Missing required columns: {', '.join(missing_cols)}"
        })
        return result
    
    # Get starting supplier number
    last_result = await db.execute(
        select(Supplier)
        .where(Supplier.client_id == client_id)
        .order_by(Supplier.supplier_number.desc())
        .limit(1)
    )
    last_supplier = last_result.scalar_one_or_none()
    
    if last_supplier and last_supplier.supplier_number.isdigit():
        current_number = int(last_supplier.supplier_number)
    else:
        current_number = 0
    
    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel row (header = 1, first data = 2)
        
        try:
            # Validate required fields
            navn = row.get('navn')
            if not navn or pd.isna(navn):
                result.errors.append({
                    "row": row_num,
                    "error": "Navn er påkrevd"
                })
                continue
            
            org_nummer = validate_org_number(row.get('org_nummer'))
            if not org_nummer:
                result.errors.append({
                    "row": row_num,
                    "error": "Ugyldig organisasjonsnummer (må være 9 siffer)"
                })
                continue
            
            # Check if supplier already exists
            existing = await db.execute(
                select(Supplier).where(
                    Supplier.client_id == client_id,
                    Supplier.org_number == org_nummer
                )
            )
            if existing.scalar_one_or_none():
                result.skipped += 1
                continue
            
            # Parse payment terms (e.g., "30 dager" -> 30)
            betalingsbetingelser = row.get('betalingsbetingelser', '30 dager')
            payment_days = 30
            if betalingsbetingelser:
                match = re.search(r'(\d+)', str(betalingsbetingelser))
                if match:
                    payment_days = int(match.group(1))
            
            # Build address
            address = {}
            if row.get('adresse'):
                address['line1'] = str(row.get('adresse'))
            if row.get('postnummer'):
                address['postal_code'] = str(row.get('postnummer'))
            if row.get('poststed'):
                address['city'] = str(row.get('poststed'))
            if row.get('land'):
                address['country'] = str(row.get('land'))
            else:
                address['country'] = 'Norge'
            
            # Build contact
            contact = {}
            if row.get('epost'):
                email = validate_email(row.get('epost'))
                if email:
                    contact['email'] = email
            if row.get('telefon'):
                phone = validate_phone(row.get('telefon'))
                if phone:
                    contact['phone'] = phone
            
            # Build financial
            financial = {
                'payment_terms_days': payment_days,
                'currency': 'NOK'
            }
            if row.get('kontonummer'):
                financial['bank_account'] = str(row.get('kontonummer'))
            
            # Generate supplier number
            current_number += 1
            supplier_number = str(current_number).zfill(5)
            
            # Create supplier
            supplier = Supplier(
                client_id=client_id,
                supplier_number=supplier_number,
                company_name=str(navn),
                org_number=org_nummer,
                address_line1=address.get('line1') if address else None,
                postal_code=address.get('postal_code') if address else None,
                city=address.get('city') if address else None,
                country=address.get('country', 'Norge') if address else 'Norge',
                email=contact.get('email') if contact else None,
                phone=contact.get('phone') if contact else None,
                bank_account=financial.get('bank_account') if financial else None,
                payment_terms_days=financial.get('payment_terms_days', 30),
                currency=financial.get('currency', 'NOK'),
                status='active'
            )
            
            db.add(supplier)
            result.created += 1
        
        except Exception as e:
            result.errors.append({
                "row": row_num,
                "error": str(e)
            })
    
    # Commit all at once
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        result.errors.append({
            "row": 0,
            "error": f"Database error: {str(e)}"
        })
        result.created = 0
    
    return result


async def import_customers(
    db: AsyncSession,
    df: pd.DataFrame,
    client_id
) -> ContactImportResult:
    """
    Bulk import customers from DataFrame
    
    Expected columns:
    - navn (required)
    - org_nummer (required for B2B)
    - epost
    - telefon
    - adresse
    - postnummer
    - poststed
    - land
    - kontonummer
    - betalingsbetingelser (e.g., "14 dager")
    - kunde_type (b2b/b2c)
    """
    result = ContactImportResult()
    
    # Validate required columns
    required_cols = ['navn']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        result.errors.append({
            "row": 0,
            "error": f"Missing required columns: {', '.join(missing_cols)}"
        })
        return result
    
    # Get starting customer number
    last_result = await db.execute(
        select(Customer)
        .where(Customer.client_id == client_id)
        .order_by(Customer.customer_number.desc())
        .limit(1)
    )
    last_customer = last_result.scalar_one_or_none()
    
    if last_customer and last_customer.customer_number.isdigit():
        current_number = int(last_customer.customer_number)
    else:
        current_number = 0
    
    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel row (header = 1, first data = 2)
        
        try:
            # Validate required fields
            navn = row.get('navn')
            if not navn or pd.isna(navn):
                result.errors.append({
                    "row": row_num,
                    "error": "Navn er påkrevd"
                })
                continue
            
            # Org number validation (optional for B2C)
            org_nummer = None
            if row.get('org_nummer'):
                org_nummer = validate_org_number(row.get('org_nummer'))
                
                # Check if customer already exists
                if org_nummer:
                    existing = await db.execute(
                        select(Customer).where(
                            Customer.client_id == client_id,
                            Customer.org_number == org_nummer
                        )
                    )
                    if existing.scalar_one_or_none():
                        result.skipped += 1
                        continue
            
            # Parse payment terms
            betalingsbetingelser = row.get('betalingsbetingelser', '14 dager')
            payment_days = 14
            if betalingsbetingelser:
                match = re.search(r'(\d+)', str(betalingsbetingelser))
                if match:
                    payment_days = int(match.group(1))
            
            # Build address
            address = {}
            if row.get('adresse'):
                address['line1'] = str(row.get('adresse'))
            if row.get('postnummer'):
                address['postal_code'] = str(row.get('postnummer'))
            if row.get('poststed'):
                address['city'] = str(row.get('poststed'))
            if row.get('land'):
                address['country'] = str(row.get('land'))
            else:
                address['country'] = 'Norge'
            
            # Build contact
            contact = {}
            if row.get('epost'):
                email = validate_email(row.get('epost'))
                if email:
                    contact['email'] = email
            if row.get('telefon'):
                phone = validate_phone(row.get('telefon'))
                if phone:
                    contact['phone'] = phone
            
            # Build financial
            financial = {
                'payment_terms_days': payment_days,
                'currency': 'NOK',
                'reminder_fee': 0
            }
            
            # Customer type
            is_company = bool(org_nummer)  # If has org_number, it's a company
            
            # Generate customer number
            current_number += 1
            customer_number = str(current_number).zfill(5)
            
            # Create customer
            customer = Customer(
                client_id=client_id,
                customer_number=customer_number,
                is_company=is_company,
                name=str(navn),
                org_number=org_nummer,
                address_line1=address.get('line1') if address else None,
                postal_code=address.get('postal_code') if address else None,
                city=address.get('city') if address else None,
                country=address.get('country', 'Norge') if address else 'Norge',
                email=contact.get('email') if contact else None,
                phone=contact.get('phone') if contact else None,
                payment_terms_days=financial.get('payment_terms_days', 14),
                currency=financial.get('currency', 'NOK'),
                reminder_fee=financial.get('reminder_fee', 0),
                use_kid=False,
                status='active'
            )
            
            db.add(customer)
            result.created += 1
        
        except Exception as e:
            result.errors.append({
                "row": row_num,
                "error": str(e)
            })
    
    # Commit all at once
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        result.errors.append({
            "row": 0,
            "error": f"Database error: {str(e)}"
        })
        result.created = 0
    
    return result
