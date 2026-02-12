"""
Contextual Help Service - AI-powered tooltips and help

Features:
1. Context-aware help texts for form fields
2. Role-based help (different for accountants vs. clients)
3. Stored in database for caching and customization
4. Simple tooltip component integration
5. Can generate help texts on-demand using AI

Help is shown when user hovers over fields or clicks ? icons.
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import uuid
from anthropic import AsyncAnthropic

from app.database import Base
from app.config import settings
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID


# Define help text model (to be added via migration)
class ContextualHelpText(Base):
    """
    Contextual Help Text
    
    Stores AI-generated help texts for form fields and UI elements
    """
    __tablename__ = "contextual_help_texts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Location identifiers
    page = Column(String(100), nullable=False, index=True)  # e.g., "vendor_invoice"
    field = Column(String(100), nullable=False, index=True)  # e.g., "invoice_number"
    
    # Role-based help
    user_role = Column(String(50), nullable=False, index=True)  # "accountant" | "client" | "all"
    
    # Help content
    help_text = Column(Text, nullable=False)  # Short tooltip text
    detailed_help = Column(Text, nullable=True)  # Longer explanation (optional)
    example_text = Column(String(255), nullable=True)  # Example value
    
    # Metadata
    language = Column(String(5), default="nb", nullable=False)  # Norwegian Bokmål
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "page": self.page,
            "field": self.field,
            "user_role": self.user_role,
            "help_text": self.help_text,
            "detailed_help": self.detailed_help,
            "example_text": self.example_text,
            "language": self.language
        }


class ContextualHelpService:
    """
    Contextual Help Service
    
    Provides context-aware help texts for UI elements
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Initialize Anthropic client if available
        self.anthropic_client = None
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Default help texts (fallback if database is empty)
        self.default_help_texts = {
            "vendor_invoice": {
                "invoice_number": {
                    "accountant": "Leverandørens fakturanummer. Brukes til referanse og oppslag.",
                    "client": "Fakturanummeret fra leverandøren.",
                    "example": "F-2024-001"
                },
                "invoice_date": {
                    "accountant": "Fakturadato. Avgjør hvilken periode fakturaen bokføres i.",
                    "client": "Datoen fakturaen ble utstedt.",
                    "example": "01.02.2024"
                },
                "due_date": {
                    "accountant": "Forfallsdato. Brukes til å beregne betalingsvarsel og forsinkelsesrenter.",
                    "client": "Når fakturaen skal betales.",
                    "example": "01.03.2024"
                },
                "account_number": {
                    "accountant": "Kontokode fra kontoplanen. Bestemmer hvor kostanden bokføres.",
                    "client": "Hvilken kostnadskonto dette gjelder (f.eks. kontorutstyr).",
                    "example": "4000 - Kontorrekvisita"
                }
            },
            "bank_reconciliation": {
                "transaction_date": {
                    "accountant": "Transaksjonsdato fra banken. Kan avvike fra bokføringsdato.",
                    "client": "Når transaksjonen skjedde.",
                    "example": "15.02.2024"
                },
                "amount": {
                    "accountant": "Beløp i NOK. Negative beløp er utgifter, positive er inntekter.",
                    "client": "Beløpet som ble betalt eller mottatt.",
                    "example": "1 500,00"
                },
                "kid_number": {
                    "accountant": "KID-nummer (Kunde-ID). Automatisk matching til fakturaer.",
                    "client": "Betalingsreferanse fra fakturaen.",
                    "example": "123456789"
                }
            },
            "general_ledger": {
                "voucher_number": {
                    "accountant": "Bilagsnummer. Sekvensiell nummerering per periode.",
                    "client": "Referansenummer for bokføringen.",
                    "example": "100"
                },
                "entry_date": {
                    "accountant": "Bokføringsdato. Avgjør hvilken periode bilaget tilhører.",
                    "client": "Når transaksjonen ble registrert.",
                    "example": "28.02.2024"
                },
                "debit": {
                    "accountant": "Debet (soll). Økning i eiendeler/kostnader, reduksjon i gjeld/inntekt.",
                    "client": "Utgiftsside av bokføringen.",
                    "example": "5 000,00"
                },
                "credit": {
                    "accountant": "Kredit (ha). Reduksjon i eiendeler/kostnader, økning i gjeld/inntekt.",
                    "client": "Inntektsside av bokføringen.",
                    "example": "5 000,00"
                }
            }
        }
    
    async def get_help_text(
        self,
        page: str,
        field: str,
        user_role: str = "client",
        language: str = "nb"
    ) -> Optional[Dict[str, Any]]:
        """
        Get contextual help text for a field
        
        Checks database first, falls back to defaults
        """
        # Try database first
        query = select(ContextualHelpText).where(
            and_(
                ContextualHelpText.page == page,
                ContextualHelpText.field == field,
                or_(
                    ContextualHelpText.user_role == user_role,
                    ContextualHelpText.user_role == "all"
                ),
                ContextualHelpText.language == language
            )
        )
        
        result = await self.db.execute(query)
        help_entry = result.scalar_one_or_none()
        
        if help_entry:
            return help_entry.to_dict()
        
        # Fall back to default help texts
        if page in self.default_help_texts:
            if field in self.default_help_texts[page]:
                field_help = self.default_help_texts[page][field]
                help_text = field_help.get(user_role) or field_help.get("client")
                
                return {
                    "page": page,
                    "field": field,
                    "user_role": user_role,
                    "help_text": help_text,
                    "example_text": field_help.get("example"),
                    "language": language
                }
        
        return None
    
    async def generate_help_text(
        self,
        page: str,
        field: str,
        user_role: str = "client",
        language: str = "nb",
        field_label: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate help text using AI
        
        Used for dynamic help or missing entries
        """
        if not self.anthropic_client:
            return None
        
        # Build context-aware prompt
        role_context = {
            "accountant": "En erfaren regnskapsfører som trenger teknisk dokumentasjon",
            "client": "En vanlig bruker uten regnskapserfaring"
        }
        
        role_desc = role_context.get(user_role, "En bruker")
        
        prompt = f"""Lag en kort, hjelpsom hjelpetekst for et feltmed i et regnskapssystem.

Side: {page}
Felt: {field}
Feltnavn: {field_label or field}
Målgruppe: {role_desc}
Språk: Norsk (bokmål)

Lag en hjelpetekst som:
1. Er kort (maks 2 setninger)
2. Forklarer hva feltet brukes til
3. Er tilpasset målgruppen
4. Bruker enkelt språk

Hvis mulig, inkluder også et eksempel på gyldig verdi.

Svar i JSON format:
{{
  "help_text": "<kort hjelpetekst>",
  "detailed_help": "<lengre forklaring (valgfri)>",
  "example_text": "<eksempelverdi>"
}}"""
        
        try:
            message = await self.anthropic_client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=500,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            response_text = message.content[0].text.strip()
            
            # Extract JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Store in database
                await self.store_help_text(
                    page=page,
                    field=field,
                    user_role=user_role,
                    help_text=result.get('help_text', ''),
                    detailed_help=result.get('detailed_help'),
                    example_text=result.get('example_text'),
                    language=language
                )
                
                return {
                    "page": page,
                    "field": field,
                    "user_role": user_role,
                    "help_text": result.get('help_text'),
                    "detailed_help": result.get('detailed_help'),
                    "example_text": result.get('example_text'),
                    "language": language
                }
            
        except Exception as e:
            print(f"Error generating help text: {e}")
            return None
    
    async def store_help_text(
        self,
        page: str,
        field: str,
        user_role: str,
        help_text: str,
        detailed_help: Optional[str] = None,
        example_text: Optional[str] = None,
        language: str = "nb"
    ) -> UUID:
        """
        Store help text in database
        
        Uses upsert to update if exists
        """
        help_id = uuid.uuid4()
        
        stmt = insert(ContextualHelpText).values(
            id=help_id,
            page=page,
            field=field,
            user_role=user_role,
            help_text=help_text,
            detailed_help=detailed_help,
            example_text=example_text,
            language=language,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ).on_conflict_do_update(
            index_elements=['page', 'field', 'user_role', 'language'],
            set_={
                'help_text': help_text,
                'detailed_help': detailed_help,
                'example_text': example_text,
                'updated_at': datetime.utcnow()
            }
        )
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        return help_id
    
    async def get_page_help_texts(
        self,
        page: str,
        user_role: str = "client",
        language: str = "nb"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all help texts for a page
        
        Returns dict keyed by field name
        """
        query = select(ContextualHelpText).where(
            and_(
                ContextualHelpText.page == page,
                or_(
                    ContextualHelpText.user_role == user_role,
                    ContextualHelpText.user_role == "all"
                ),
                ContextualHelpText.language == language
            )
        )
        
        result = await self.db.execute(query)
        help_texts = result.scalars().all()
        
        # Convert to dict
        help_dict = {}
        for help_entry in help_texts:
            help_dict[help_entry.field] = help_entry.to_dict()
        
        # Merge with defaults if fields are missing
        if page in self.default_help_texts:
            for field, field_help in self.default_help_texts[page].items():
                if field not in help_dict:
                    help_text = field_help.get(user_role) or field_help.get("client")
                    help_dict[field] = {
                        "page": page,
                        "field": field,
                        "user_role": user_role,
                        "help_text": help_text,
                        "example_text": field_help.get("example"),
                        "language": language
                    }
        
        return help_dict
    
    async def bulk_generate_help_texts(
        self,
        pages_and_fields: List[Tuple[str, str, str]],  # (page, field, label)
        user_roles: List[str] = ["accountant", "client"]
    ) -> Dict[str, Any]:
        """
        Bulk generate help texts for multiple fields
        
        Useful for populating database initially
        """
        if not self.anthropic_client:
            return {"error": "AI client not configured"}
        
        generated_count = 0
        failed_count = 0
        
        for page, field, label in pages_and_fields:
            for role in user_roles:
                try:
                    result = await self.generate_help_text(
                        page=page,
                        field=field,
                        user_role=role,
                        field_label=label
                    )
                    if result:
                        generated_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    print(f"Failed to generate help for {page}.{field}: {e}")
                    failed_count += 1
        
        return {
            "total_requested": len(pages_and_fields) * len(user_roles),
            "generated": generated_count,
            "failed": failed_count
        }


# Helper functions
async def get_field_help(
    db: AsyncSession,
    page: str,
    field: str,
    user_role: str = "client"
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get help text for a field
    """
    service = ContextualHelpService(db)
    return await service.get_help_text(page, field, user_role)


async def get_all_page_help(
    db: AsyncSession,
    page: str,
    user_role: str = "client"
) -> Dict[str, Dict[str, Any]]:
    """
    Get all help texts for a page
    """
    service = ContextualHelpService(db)
    return await service.get_page_help_texts(page, user_role)


# Populate initial help texts
INITIAL_HELP_DATA = [
    # Vendor Invoice fields
    ("vendor_invoice", "invoice_number", "Fakturanummer"),
    ("vendor_invoice", "invoice_date", "Fakturadato"),
    ("vendor_invoice", "due_date", "Forfallsdato"),
    ("vendor_invoice", "amount_excl_vat", "Beløp ekskl. MVA"),
    ("vendor_invoice", "vat_amount", "MVA-beløp"),
    ("vendor_invoice", "total_amount", "Totalt beløp"),
    ("vendor_invoice", "account_number", "Konto"),
    
    # Bank Reconciliation fields
    ("bank_reconciliation", "transaction_date", "Transaksjonsdato"),
    ("bank_reconciliation", "amount", "Beløp"),
    ("bank_reconciliation", "description", "Beskrivelse"),
    ("bank_reconciliation", "kid_number", "KID-nummer"),
    
    # General Ledger fields
    ("general_ledger", "voucher_number", "Bilagsnummer"),
    ("general_ledger", "entry_date", "Bokføringsdato"),
    ("general_ledger", "description", "Beskrivelse"),
    ("general_ledger", "debit", "Debet"),
    ("general_ledger", "credit", "Kredit"),
]
