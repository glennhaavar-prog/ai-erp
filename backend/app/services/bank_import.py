"""
Bank Statement Import Service
Parse CSV and MT940 formats from Norwegian banks
"""
import csv
import io
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.bank_transaction import BankTransaction, TransactionType, TransactionStatus
import logging

logger = logging.getLogger(__name__)


class BankImportService:
    """Service for importing bank statements"""
    
    @staticmethod
    def parse_norwegian_csv(
        file_content: str,
        client_id: uuid.UUID,
        upload_batch_id: uuid.UUID,
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        Parse Norwegian bank CSV format
        
        Common formats:
        - DNB: "Dato","Forklaring","Rentedato","Ut fra konto","Inn på konto","Saldo"
        - Sparebank1: "Bokføringsdato","Beløp","Beskrivelse","Kontonummer","Arkivreferanse"
        
        Args:
            file_content: CSV file content as string
            client_id: Client UUID
            upload_batch_id: Batch identifier for this upload
            filename: Original filename
            
        Returns:
            List of transaction dictionaries ready for database insert
        """
        transactions = []
        reader = csv.DictReader(io.StringIO(file_content), delimiter=';')
        
        for row in reader:
            try:
                # Parse transaction (flexible for different bank formats)
                trans_data = BankImportService._parse_csv_row(row, client_id, upload_batch_id, filename)
                if trans_data:
                    transactions.append(trans_data)
            except Exception as e:
                logger.error(f"Error parsing row: {row}, error: {str(e)}")
                continue
        
        return transactions
    
    @staticmethod
    def _parse_csv_row(row: Dict[str, str], client_id: uuid.UUID, upload_batch_id: uuid.UUID, filename: str) -> Dict[str, Any]:
        """
        Parse a single CSV row into transaction data
        Flexible parser for common Norwegian bank formats
        """
        # Try to find date column
        date_str = (
            row.get('Dato') or 
            row.get('Bokføringsdato') or 
            row.get('Bokført') or
            row.get('Transaction Date')
        )
        
        if not date_str:
            return None
        
        # Parse date (try different formats)
        transaction_date = BankImportService._parse_date(date_str)
        if not transaction_date:
            return None
        
        # Amount parsing
        amount_in = row.get('Inn på konto') or row.get('Kredit') or row.get('Credit') or '0'
        amount_out = row.get('Ut fra konto') or row.get('Debet') or row.get('Debit') or '0'
        amount_str = row.get('Beløp') or row.get('Amount')
        
        # Determine amount and type
        if amount_str:
            # Amount is in single column (negative = out, positive = in)
            amount_val = BankImportService._parse_amount(amount_str)
            transaction_type = TransactionType.CREDIT if amount_val > 0 else TransactionType.DEBIT
            amount = abs(amount_val)
        else:
            # Separate in/out columns
            amount_in_val = BankImportService._parse_amount(amount_in)
            amount_out_val = BankImportService._parse_amount(amount_out)
            
            if amount_in_val > 0:
                transaction_type = TransactionType.CREDIT
                amount = amount_in_val
            else:
                transaction_type = TransactionType.DEBIT
                amount = amount_out_val
        
        # Description
        description = (
            row.get('Forklaring') or 
            row.get('Beskrivelse') or 
            row.get('Tekst') or
            row.get('Description') or
            'Unknown transaction'
        )
        
        # Account
        bank_account = (
            row.get('Kontonummer') or
            row.get('Account') or
            'UNKNOWN'
        )
        
        # Reference/KID
        kid_number = row.get('KID') or row.get('Arkivreferanse')
        reference_number = row.get('Referanse') or row.get('Reference')
        
        # Balance after
        balance_str = row.get('Saldo') or row.get('Balance')
        balance_after = BankImportService._parse_amount(balance_str) if balance_str else None
        
        return {
            "client_id": client_id,
            "transaction_date": transaction_date,
            "amount": amount,
            "transaction_type": transaction_type,
            "description": description.strip(),
            "bank_account": bank_account,
            "kid_number": kid_number,
            "reference_number": reference_number,
            "balance_after": balance_after,
            "status": TransactionStatus.UNMATCHED,
            "upload_batch_id": upload_batch_id,
            "original_filename": filename,
        }
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse date from various formats"""
        date_formats = [
            '%d.%m.%Y',      # Norwegian: 31.12.2023
            '%Y-%m-%d',      # ISO: 2023-12-31
            '%d/%m/%Y',      # 31/12/2023
            '%d-%m-%Y',      # 31-12-2023
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    @staticmethod
    def _parse_amount(amount_str: str) -> Decimal:
        """Parse amount from Norwegian format (123.456,78 or 123456.78)"""
        if not amount_str or amount_str.strip() == '':
            return Decimal('0.00')
        
        # Remove spaces and handle Norwegian format
        amount_str = amount_str.strip().replace(' ', '').replace('\xa0', '')
        
        # Handle Norwegian format: 1.234,56 -> 1234.56
        if ',' in amount_str and '.' in amount_str:
            # Both comma and dot present
            if amount_str.rindex(',') > amount_str.rindex('.'):
                # Comma is decimal separator
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                # Dot is decimal separator
                amount_str = amount_str.replace(',', '')
        elif ',' in amount_str:
            # Only comma (assume decimal separator)
            amount_str = amount_str.replace(',', '.')
        
        return Decimal(amount_str)
    
    @staticmethod
    async def import_transactions(
        db: AsyncSession,
        transactions: List[Dict[str, Any]]
    ) -> int:
        """
        Bulk insert bank transactions into database
        
        Args:
            db: Database session
            transactions: List of transaction dictionaries
            
        Returns:
            Number of transactions imported
        """
        count = 0
        for trans_data in transactions:
            try:
                transaction = BankTransaction(**trans_data)
                db.add(transaction)
                count += 1
            except Exception as e:
                logger.error(f"Error inserting transaction: {str(e)}")
                continue
        
        await db.commit()
        logger.info(f"Imported {count} bank transactions")
        return count
