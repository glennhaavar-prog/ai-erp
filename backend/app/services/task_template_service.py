"""
Task Template Service - AI-foreslåtte oppgaver
"""
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date, datetime
from calendar import monthrange

from app.models.task import Task, TaskCategory, TaskFrequency, TaskStatus
from app.models.task_audit_log import TaskAuditLog, TaskAuditAction
from app.models.client import Client


class TaskTemplateService:
    """
    Service for generating AI-suggested task templates
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_templates(self, client_id: UUID, period_type: str = "monthly") -> List[dict]:
        """
        Generate task templates based on client profile
        
        AI-suggested tasks based on:
        - Client profile (mva-pliktig? ansatte? bransje?)
        - Lovkrav (alle trenger bankavstemming, mva-oppgave hvis pliktig)
        - Period type (monthly/quarterly/yearly)
        """
        # Get client
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return []
        
        templates = []
        
        # Standardoppgaver for alle klienter (månedlig)
        if period_type == "monthly":
            templates.extend(self._get_monthly_templates(client))
        elif period_type == "quarterly":
            templates.extend(self._get_quarterly_templates(client))
        elif period_type == "yearly":
            templates.extend(self._get_yearly_templates(client))
        
        return templates
    
    def _get_monthly_templates(self, client: Client) -> List[dict]:
        """Get monthly task templates"""
        templates = []
        
        # Bokføring (standard for alle)
        bokforing_tasks = [
            {
                "name": "Inngående fakturaer bokført",
                "description": "Alle innkommende fakturaer fra leverandører bokført",
                "category": TaskCategory.BOKFØRING,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 10
            },
            {
                "name": "Utgående fakturaer bokført",
                "description": "Alle utgående fakturaer til kunder bokført",
                "category": TaskCategory.BOKFØRING,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 20
            },
            {
                "name": "Bank importert og bokført",
                "description": "Banktransaksjoner importert og bokført",
                "category": TaskCategory.BOKFØRING,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 30
            },
        ]
        
        # Add lønn if client has employees
        # Note: We don't have employee count in client model yet, but we can add this logic later
        bokforing_tasks.append({
            "name": "Lønn bokført",
            "description": "Lønnstransaksjoner bokført",
            "category": TaskCategory.BOKFØRING,
            "frequency": TaskFrequency.MONTHLY,
            "sort_order": 40
        })
        
        templates.extend(bokforing_tasks)
        
        # Avstemming (standard for alle)
        avstemming_tasks = [
            {
                "name": "Bankavstemming",
                "description": "Avstemming mellom bank og bokføring",
                "category": TaskCategory.AVSTEMMING,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 50
            },
            {
                "name": "Avstemming kundefordringer (1500)",
                "description": "Avstemming av kundefordringer mot reskontro",
                "category": TaskCategory.AVSTEMMING,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 60
            },
            {
                "name": "Avstemming leverandørgjeld (2400)",
                "description": "Avstemming av leverandørgjeld mot reskontro",
                "category": TaskCategory.AVSTEMMING,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 70
            },
            {
                "name": "Avstemming skyldig skattetrekk (2600)",
                "description": "Avstemming av skyldig skattetrekk",
                "category": TaskCategory.AVSTEMMING,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 80
            },
        ]
        templates.extend(avstemming_tasks)
        
        # Rapportering
        rapportering_tasks = [
            {
                "name": "Resultatregnskap gjennomgått",
                "description": "Resultatregnskap for perioden gjennomgått og kvalitetssikret",
                "category": TaskCategory.RAPPORTERING,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 90
            },
        ]
        
        # MVA if applicable (we assume all clients are VAT-registered for now)
        # In production, check client.vat_registered or similar field
        rapportering_tasks.extend([
            {
                "name": "Mva-oppgave kontrollert",
                "description": "Mva-oppgave for perioden kontrollert",
                "category": TaskCategory.COMPLIANCE,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 100
            },
            {
                "name": "Mva-oppgave sendt",
                "description": "Mva-oppgave sendt til Altinn",
                "category": TaskCategory.COMPLIANCE,
                "frequency": TaskFrequency.MONTHLY,
                "sort_order": 110
            },
        ])
        
        templates.extend(rapportering_tasks)
        
        return templates
    
    def _get_quarterly_templates(self, client: Client) -> List[dict]:
        """Get quarterly task templates"""
        return [
            {
                "name": "Kvartalsrapport utarbeidet",
                "description": "Kvartalsrapport med resultat og balanse",
                "category": TaskCategory.RAPPORTERING,
                "frequency": TaskFrequency.QUARTERLY,
                "sort_order": 10
            },
        ]
    
    def _get_yearly_templates(self, client: Client) -> List[dict]:
        """Get yearly task templates"""
        return [
            {
                "name": "Årsoppgjør utarbeidet",
                "description": "Årsregnskap og årsberetning",
                "category": TaskCategory.RAPPORTERING,
                "frequency": TaskFrequency.YEARLY,
                "sort_order": 10
            },
            {
                "name": "Skattemelding kontrollert",
                "description": "Skattemelding for selskapet kontrollert",
                "category": TaskCategory.COMPLIANCE,
                "frequency": TaskFrequency.YEARLY,
                "sort_order": 20
            },
            {
                "name": "Skattemelding sendt",
                "description": "Skattemelding sendt til Skatteetaten",
                "category": TaskCategory.COMPLIANCE,
                "frequency": TaskFrequency.YEARLY,
                "sort_order": 30
            },
        ]
    
    def apply_template(
        self, 
        client_id: UUID, 
        period_year: int, 
        period_month: int = None
    ) -> List[Task]:
        """
        Apply template to create actual tasks for a period
        """
        # Determine period type
        if period_month:
            period_type = "monthly"
        else:
            period_type = "yearly"
        
        # Get templates
        templates = self.generate_templates(client_id, period_type)
        
        # Calculate due date (last day of the period)
        if period_month:
            _, last_day = monthrange(period_year, period_month)
            due_date = date(period_year, period_month, last_day)
        else:
            due_date = date(period_year, 12, 31)
        
        # Create tasks
        created_tasks = []
        for template in templates:
            task = Task(
                client_id=client_id,
                name=template["name"],
                description=template.get("description"),
                category=template.get("category"),
                frequency=template.get("frequency"),
                period_year=period_year,
                period_month=period_month,
                due_date=due_date,
                status=TaskStatus.NOT_STARTED,
                sort_order=template.get("sort_order")
            )
            self.db.add(task)
            self.db.flush()
            
            # Create audit log
            audit_log = TaskAuditLog(
                task_id=task.id,
                action=TaskAuditAction.CREATED,
                performed_by="AI-agent",
                performed_at=datetime.utcnow(),
                result_description=f"Auto-created task from template"
            )
            self.db.add(audit_log)
            
            created_tasks.append(task)
        
        self.db.commit()
        
        return created_tasks
