"""
Natural Language Query (NLQ) Service

Allows users to query accounting data using natural language.
Claude converts NL → SQL, we execute safely.
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
from app.config import settings
import anthropic


class NLQService:
    """Natural Language Query service - converts questions to SQL"""
    
    def __init__(self):
        api_key = settings.ANTHROPIC_API_KEY if hasattr(settings, 'ANTHROPIC_API_KEY') else None
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5"
    
    async def parse_and_execute(
        self,
        question: str,
        client_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Parse natural language question to SQL and execute.
        
        Args:
            question: Natural language question
            client_id: Client UUID for filtering
            db: Database session
        
        Returns:
            Dict with question, SQL, results, count
        """
        
        # Get database schema info
        schema = self._get_schema_info()
        
        # Ask Claude to generate SQL
        sql = await self._generate_sql(question, schema, client_id)
        
        # Validate (must be SELECT only!)
        if not self._is_safe_query(sql):
            raise ValueError("Unsafe query detected. Only SELECT queries are allowed.")
        
        # Execute query
        try:
            result = await db.execute(text(sql))
            rows = result.fetchall()
            
            # Convert to list of dicts
            results = []
            if rows:
                columns = result.keys()
                results = [dict(zip(columns, row)) for row in rows]
            
            return {
                "success": True,
                "question": question,
                "sql": sql,
                "results": results,
                "count": len(results)
            }
        
        except Exception as e:
            return {
                "success": False,
                "question": question,
                "sql": sql,
                "error": str(e),
                "results": [],
                "count": 0
            }
    
    async def _generate_sql(self, question: str, schema: str, client_id: UUID) -> str:
        """
        Use Claude to generate SQL from natural language.
        
        Args:
            question: User's question
            schema: Database schema description
            client_id: Client UUID for filtering
        
        Returns:
            SQL query string
        """
        
        system_prompt = f"""You are a SQL query generator for an accounting system.

Database schema:
{schema}

Rules:
1. Generate ONLY SELECT queries (read-only)
2. Always filter by client_id = '{client_id}'
3. Use PostgreSQL syntax
4. Return ONLY the SQL query, no explanation
5. Use Norwegian column aliases when appropriate
6. Join tables when needed for complete answers

Common patterns:
- "fakturaer fra X" → JOIN vendor_invoices with vendors
- "hvor mye" → Use SUM()
- "siste måned" → WHERE date >= CURRENT_DATE - INTERVAL '1 month'
- "i år" → WHERE EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM CURRENT_DATE)

Output format: Just the SQL query, nothing else."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=system_prompt,
            messages=[
                {"role": "user", "content": question}
            ]
        )
        
        sql = response.content[0].text.strip()
        
        # Clean up (remove markdown code blocks if present)
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        return sql
    
    def _is_safe_query(self, sql: str) -> bool:
        """
        Validate that query is read-only.
        
        Args:
            sql: SQL query string
        
        Returns:
            True if safe, False otherwise
        """
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith("SELECT"):
            return False
        
        # Block dangerous keywords
        dangerous = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
            "CREATE", "TRUNCATE", "GRANT", "REVOKE", "EXEC"
        ]
        
        if any(kw in sql_upper for kw in dangerous):
            return False
        
        return True
    
    def _get_schema_info(self) -> str:
        """
        Get database schema description for Claude.
        
        Returns:
            Schema description string
        """
        
        return """
## Tables

### general_ledger
- id (UUID)
- client_id (UUID) - ALWAYS filter by this!
- accounting_date (DATE)
- entry_date (DATE)
- period (VARCHAR) - Format: YYYY-MM
- fiscal_year (INTEGER)
- voucher_number (VARCHAR)
- voucher_series (VARCHAR)
- description (TEXT)
- source_type (VARCHAR)
- created_by_type (VARCHAR)
- status (VARCHAR)

### general_ledger_lines
- id (UUID)
- general_ledger_id (UUID)
- account_number (VARCHAR)
- debit_amount (NUMERIC)
- credit_amount (NUMERIC)
- line_description (TEXT)

### vendor_invoices
- id (UUID)
- client_id (UUID) - ALWAYS filter by this!
- vendor_id (UUID)
- invoice_number (VARCHAR)
- invoice_date (DATE)
- due_date (DATE)
- amount_excl_vat (NUMERIC)
- vat_amount (NUMERIC)
- total_amount (NUMERIC)
- payment_status (VARCHAR)
- review_status (VARCHAR)

### vendors
- id (UUID)
- client_id (UUID)
- name (VARCHAR)
- org_number (VARCHAR)

### accruals
- id (UUID)
- client_id (UUID) - ALWAYS filter by this!
- description (TEXT)
- from_date (DATE)
- to_date (DATE)
- total_amount (NUMERIC)
- balance_account (VARCHAR)
- result_account (VARCHAR)
- frequency (VARCHAR)
- status (VARCHAR)

### clients
- id (UUID)
- name (VARCHAR)
- org_number (VARCHAR)
- base_currency (VARCHAR)

## Example Queries

Q: "Vis meg alle fakturaer fra Telenor"
A: SELECT vi.* FROM vendor_invoices vi JOIN vendors v ON vi.vendor_id = v.id WHERE vi.client_id = '{client_id}' AND v.name ILIKE '%Telenor%'

Q: "Hvor mye har vi brukt på forsikring i år?"
A: SELECT SUM(total_amount) as total FROM accruals WHERE client_id = '{client_id}' AND description ILIKE '%forsikring%' AND EXTRACT(YEAR FROM from_date) = EXTRACT(YEAR FROM CURRENT_DATE)

Q: "Siste 10 bilag"
A: SELECT voucher_number, accounting_date, description FROM general_ledger WHERE client_id = '{client_id}' ORDER BY accounting_date DESC LIMIT 10
"""
