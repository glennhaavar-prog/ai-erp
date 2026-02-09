"""
Test Data Generator Service

Generates realistic test data for demo environment:
- Supplier invoices (EHF XML format)
- Bank transactions (CSV simulation)
- Customer invoices (JSON)
- Edge cases (high/low confidence, duplicates, unmatched)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.vendor_invoice import VendorInvoice
from app.models.customer_invoice import CustomerInvoice
from app.models.bank_transaction import BankTransaction
from app.models.chart_of_accounts import Account
from datetime import datetime, timedelta
from decimal import Decimal
import random
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)


# Task status storage (in-memory for now, could be Redis)
_task_statuses = {}


class TestDataGeneratorService:
    """Service for generating test data"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_task_status(self, task_id: str) -> dict | None:
        """Get task status"""
        return _task_statuses.get(task_id)
    
    def _update_task_status(self, task_id: str, status: str, **kwargs):
        """Update task status"""
        if task_id not in _task_statuses:
            _task_statuses[task_id] = {
                "task_id": task_id,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
            }
        
        _task_statuses[task_id]["status"] = status
        _task_statuses[task_id]["updated_at"] = datetime.utcnow().isoformat()
        _task_statuses[task_id].update(kwargs)
    
    async def generate_test_data(self, task_id: str, config: dict):
        """
        Generate test data based on configuration
        
        Runs as a background task
        """
        try:
            self._update_task_status(task_id, "running", progress=0, message="Starting test data generation...")
            
            # Get demo clients
            result = await self.db.execute(
                select(Client).where(Client.is_demo == True).limit(config.get("num_clients", 15))
            )
            demo_clients = result.scalars().all()
            
            if not demo_clients:
                self._update_task_status(task_id, "failed", message="No demo clients found")
                return
            
            total_steps = len(demo_clients) * 3  # vendors, invoices, transactions
            current_step = 0
            
            stats = {
                "vendors_created": 0,
                "vendor_invoices_created": 0,
                "customer_invoices_created": 0,
                "bank_transactions_created": 0,
            }
            
            for client in demo_clients:
                # Step 1: Create vendors for this client
                self._update_task_status(
                    task_id,
                    "running",
                    progress=int((current_step / total_steps) * 100),
                    message=f"Creating vendors for {client.name}..."
                )
                vendors = await self._create_vendors_for_client(client)
                stats["vendors_created"] += len(vendors)
                current_step += 1
                
                # Step 2: Create invoices
                self._update_task_status(
                    task_id,
                    "running",
                    progress=int((current_step / total_steps) * 100),
                    message=f"Creating invoices for {client.name}..."
                )
                
                # Vendor invoices
                vendor_invoices = await self._create_vendor_invoices(
                    client,
                    vendors,
                    count=config.get("invoices_per_client", 20),
                    high_confidence_ratio=config.get("high_confidence_ratio", 0.7),
                    include_duplicates=config.get("include_duplicates", True),
                    include_edge_cases=config.get("include_edge_cases", True),
                )
                stats["vendor_invoices_created"] += len(vendor_invoices)
                
                # Customer invoices
                customer_invoices = await self._create_customer_invoices(
                    client,
                    count=config.get("customer_invoices_per_client", 10),
                )
                stats["customer_invoices_created"] += len(customer_invoices)
                current_step += 1
                
                # Step 3: Create bank transactions
                self._update_task_status(
                    task_id,
                    "running",
                    progress=int((current_step / total_steps) * 100),
                    message=f"Creating bank transactions for {client.name}..."
                )
                transactions = await self._create_bank_transactions(
                    client,
                    count=config.get("transactions_per_client", 30),
                    invoices=vendor_invoices + customer_invoices,
                )
                stats["bank_transactions_created"] += len(transactions)
                current_step += 1
                
                # Commit after each client
                await self.db.commit()
            
            # Complete
            self._update_task_status(
                task_id,
                "completed",
                progress=100,
                message="Test data generation completed successfully",
                stats=stats,
                completed_at=datetime.utcnow().isoformat(),
            )
            
            logger.info(f"Test data generation completed: {stats}")
            
        except Exception as e:
            logger.error(f"Error in test data generation: {e}", exc_info=True)
            self._update_task_status(
                task_id,
                "failed",
                message=f"Error: {str(e)}",
                error=str(e),
            )
            await self.db.rollback()
    
    async def _create_vendors_for_client(self, client: Client) -> list[Vendor]:
        """Create realistic Norwegian vendors for a client"""
        
        vendor_names = [
            "Microsoft Norge AS",
            "Amazon Web Services EMEA",
            "Telenor Norge AS",
            "Equinor ASA",
            "Rema 1000 AS",
            "Coop Norge SA",
            "DNB Bank ASA",
            "Posten Norge AS",
            "Schibsted ASA",
            "Elkjøp Nordic AS",
            "Circle K Norge AS",
            "Norgesgruppen ASA",
            "Sopra Steria AS",
            "Accenture Norge AS",
            "KPMG AS",
            "PwC AS",
            "Deloitte AS",
            "EY Norge AS",
            "Visma AS",
            "Atea ASA",
        ]
        
        vendors = []
        
        # Randomly select 5-8 vendors per client for variety
        num_vendors = random.randint(5, 8)
        selected_vendors = random.sample(vendor_names, min(num_vendors, len(vendor_names)))
        
        for i, name in enumerate(selected_vendors):
            # Generate realistic Norwegian org numbers (9 digits)
            org_number = f"9{random.randint(10000000, 99999999)}"
            
            # Create realistic email based on company name
            email_domain = name.lower().replace(' ', '').replace('.', '').replace('as', '').replace('asa', '').replace('sa', '')
            email_domain = ''.join(c for c in email_domain if c.isalnum())[:15]  # Limit length
            
            vendor = Vendor(
                id=uuid.uuid4(),
                client_id=client.id,
                name=name,
                org_number=org_number,
                email=f"faktura@{email_domain}.no",
                payment_terms_days=random.choice([14, 30, 45, 60]),  # Varied payment terms
                is_active=True,
            )
            self.db.add(vendor)
            vendors.append(vendor)
        
        await self.db.flush()
        return vendors
    
    async def _create_vendor_invoices(
        self,
        client: Client,
        vendors: list[Vendor],
        count: int,
        high_confidence_ratio: float,
        include_duplicates: bool,
        include_edge_cases: bool,
    ) -> list[VendorInvoice]:
        """Create vendor invoices with varying confidence levels"""
        
        invoices = []
        base_date = datetime.utcnow() - timedelta(days=90)
        
        # Get client accounts for booking suggestions
        result = await self.db.execute(
            select(Account).where(Account.client_id == client.id)
        )
        accounts = result.scalars().all()
        expense_accounts = [a for a in accounts if a.account_type == "expense"]
        
        for i in range(count):
            vendor = random.choice(vendors)
            invoice_date = base_date + timedelta(days=random.randint(0, 90))
            
            # Determine confidence level
            if random.random() < high_confidence_ratio:
                # High confidence (85-98%)
                confidence = random.uniform(85, 98)
                review_status = "auto_approved"
                booked = True
                description = random.choice([
                    "Programvarelisens fornyelse",  # Software license renewal
                    "Sky-tjenester og hosting",  # Cloud hosting services
                    "Kontorrekvisita og forbruksmateriell",  # Office supplies
                    "Markedsføringstjenester",  # Marketing services
                    "Konsulenttjenester",  # Consulting services
                    "IT-support og vedlikehold",  # IT support and maintenance
                    "Kontorleie og felleskostnader",  # Office rent and common costs
                    "Telefoni og internett",  # Telephony and internet
                    "Strøm og oppvarming",  # Electricity and heating
                    "Forsikringer",  # Insurance
                    "Revisjon og regnskapstjenester",  # Audit and accounting services
                    "Juridiske tjenester",  # Legal services
                ])
            else:
                # Low confidence (35-75%)
                confidence = random.uniform(35, 75)
                review_status = "needs_review"
                booked = False
                description = random.choice([
                    "Diverse kostnader",  # Miscellaneous expenses
                    "Ukjent tjeneste",  # Unknown service
                    "Faktura uten beskrivelse",  # Invoice without description
                    "Konsulent - uklar kategori",  # Consulting - unclear category
                    "Representasjon",  # Representation (unclear)
                    "Forskjellige utgifter",  # Various expenses
                    "Annet",  # Other
                    "Kostnader uten spesifikasjon",  # Costs without specification
                ])
            
            amount_excl_vat = Decimal(random.randint(500, 50000))
            vat_amount = amount_excl_vat * Decimal("0.25")  # 25% Norwegian VAT
            total_amount = amount_excl_vat + vat_amount
            
            # Create AI booking suggestion
            suggested_account = random.choice(expense_accounts) if expense_accounts else None
            ai_booking_suggestion = {
                "account_number": suggested_account.account_number if suggested_account else "6000",
                "account_name": suggested_account.account_name if suggested_account else "Kontorkostnader",
                "amount": float(amount_excl_vat),
                "vat_code": "3",
                "confidence": float(confidence),
            } if suggested_account else None
            
            invoice = VendorInvoice(
                id=uuid.uuid4(),
                client_id=client.id,
                vendor_id=vendor.id,
                invoice_number=f"INV-{vendor.name[:3].upper()}-{1000 + i}",
                invoice_date=invoice_date.date(),
                due_date=(invoice_date + timedelta(days=30)).date(),
                amount_excl_vat=amount_excl_vat,
                vat_amount=vat_amount,
                total_amount=total_amount,
                currency="NOK",
                review_status=review_status,
                ai_processed=True,
                ai_confidence_score=int(confidence),
                ai_booking_suggestion=ai_booking_suggestion,
                ai_detected_category=description,
                booked_at=invoice_date if booked else None,
            )
            
            self.db.add(invoice)
            invoices.append(invoice)
        
        # Add duplicates if requested
        if include_duplicates and invoices:
            for _ in range(2):
                original = random.choice(invoices)
                duplicate = VendorInvoice(
                    id=uuid.uuid4(),
                    client_id=original.client_id,
                    vendor_id=original.vendor_id,
                    invoice_number=original.invoice_number,  # Same invoice number!
                    invoice_date=original.invoice_date,
                    due_date=original.due_date,
                    amount_excl_vat=original.amount_excl_vat,
                    vat_amount=original.vat_amount,
                    total_amount=original.total_amount,
                    currency=original.currency,
                    review_status="needs_review",
                    ai_processed=True,
                    ai_confidence_score=25,  # Low confidence for duplicate
                    ai_detected_category=f"{original.ai_detected_category} [DUPLIKAT]",
                    ai_detected_issues=["duplicate"],
                )
                self.db.add(duplicate)
                invoices.append(duplicate)
        
        await self.db.flush()
        return invoices
    
    async def _create_customer_invoices(self, client: Client, count: int) -> list[CustomerInvoice]:
        """Create customer invoices (outgoing)"""
        
        invoices = []
        base_date = datetime.utcnow() - timedelta(days=60)
        
        customer_names = [
            "Bergen Seafood AS",
            "Oslo Consulting Group AS",
            "Trondheim Technology AS",
            "Stavanger Marine Services AS",
            "Kristiansand Handel AS",
            "Drammen Distribution AS",
            "Fredrikstad Logistics AS",
            "Tromsø Arctic Solutions AS",
            "Ålesund Maritime AS",
            "Bodø Export AS",
            "Molde Industri AS",
            "Haugesund Shipping AS",
            "Sandefjord Services AS",
            "Lillehammer Trading AS",
            "Moss Construction AS",
        ]
        
        for i in range(count):
            invoice_date = base_date + timedelta(days=random.randint(0, 60))
            customer_name = random.choice(customer_names)
            
            amount_excl_vat = Decimal(random.randint(10000, 100000))
            vat_amount = amount_excl_vat * Decimal("0.25")
            total_amount = amount_excl_vat + vat_amount
            
            invoice = CustomerInvoice(
                id=uuid.uuid4(),
                client_id=client.id,
                customer_name=customer_name,
                customer_org_number=f"99{8000000 + i:07d}",
                invoice_number=f"OUT-{client.client_number}-{2000 + i}",
                invoice_date=invoice_date.date(),
                due_date=(invoice_date + timedelta(days=30)).date(),
                amount_excl_vat=amount_excl_vat,
                vat_amount=vat_amount,
                total_amount=total_amount,
                currency="NOK",
                description="Consulting services rendered",
                payment_status="unpaid" if random.random() > 0.5 else "paid",
            )
            
            if invoice.payment_status == "paid":
                invoice.paid_amount = total_amount
                invoice.payment_date = (invoice_date + timedelta(days=random.randint(10, 25))).date()
            
            self.db.add(invoice)
            invoices.append(invoice)
        
        await self.db.flush()
        return invoices
    
    async def _create_bank_transactions(
        self,
        client: Client,
        count: int,
        invoices: list,
    ) -> list[BankTransaction]:
        """Create bank transactions, some matching invoices"""
        
        transactions = []
        base_date = datetime.utcnow() - timedelta(days=60)
        
        # 70% of transactions should match invoices
        matched_count = int(count * 0.7)
        unmatched_count = count - matched_count
        
        # Create matched transactions
        for i in range(min(matched_count, len(invoices))):
            invoice = invoices[i]
            transaction_date = invoice.invoice_date + timedelta(days=random.randint(5, 20))
            
            transaction = BankTransaction(
                id=uuid.uuid4(),
                client_id=client.id,
                transaction_date=transaction_date,
                amount=float(invoice.total_amount),
                description=f"Payment: {invoice.invoice_number}",
                reference=invoice.invoice_number,
                is_matched=True,
                matched_invoice_id=invoice.id,
            )
            
            self.db.add(transaction)
            transactions.append(transaction)
        
        # Create unmatched transactions
        for i in range(unmatched_count):
            transaction_date = base_date + timedelta(days=random.randint(0, 60))
            
            transaction = BankTransaction(
                id=uuid.uuid4(),
                client_id=client.id,
                transaction_date=transaction_date,
                amount=float(Decimal(random.randint(100, 20000))),
                description=random.choice([
                    "Minibank uttak",  # ATM Withdrawal
                    "Kortbetaling",  # Card payment
                    "Overføring",  # Transfer
                    "Bankgebyr",  # Bank fee
                    "Renteinntekt",  # Interest income
                    "Lønn utbetalt",  # Salary paid
                    "Skattetrekk",  # Tax deduction
                    "Strømavgift",  # Electricity bill
                    "Forsikringspremie",  # Insurance premium
                    "Avtalegiro",  # AvtaleGiro (automatic payment)
                    "Vipps betaling",  # Vipps payment
                    "BankAxept betaling",  # BankAxept payment
                ]),
                is_matched=False,
            )
            
            self.db.add(transaction)
            transactions.append(transaction)
        
        await self.db.flush()
        return transactions
