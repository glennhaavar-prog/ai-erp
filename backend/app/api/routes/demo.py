"""
Demo Environment API Routes

Endpoints for managing demo environment:
- GET /api/demo/status - Get demo environment stats
- POST /api/demo/reset - Reset demo data
- POST /api/demo/run-test - Generate test data
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.demo import require_demo_mode
from app.services.demo.reset_service import DemoResetService
from pydantic import BaseModel, Field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


# Request/Response Models
class DemoStatusResponse(BaseModel):
    """Demo environment status"""
    demo_environment_exists: bool
    tenant: Optional[dict] = None
    stats: Optional[dict] = None
    last_reset: Optional[str] = None
    message: Optional[str] = None


class DemoResetResponse(BaseModel):
    """Demo reset response"""
    success: bool
    message: str
    deleted_counts: dict
    reset_at: str
    clients_preserved: int


class TestDataConfig(BaseModel):
    """Configuration for test data generation"""
    num_clients: int = Field(default=15, ge=1, le=50, description="Number of clients (default: use existing)")
    invoices_per_client: int = Field(default=20, ge=1, le=100, description="Vendor invoices per client")
    customer_invoices_per_client: int = Field(default=10, ge=0, le=50, description="Customer invoices per client")
    transactions_per_client: int = Field(default=30, ge=1, le=150, description="Bank transactions per client")
    high_confidence_ratio: float = Field(default=0.7, ge=0.0, le=1.0, description="Ratio of high-confidence items")
    include_duplicates: bool = Field(default=True, description="Include duplicate invoices")
    include_edge_cases: bool = Field(default=True, description="Include edge cases (low confidence, unmatched)")


class TestDataRunResponse(BaseModel):
    """Test data generation response"""
    task_id: str
    status: str
    message: str
    config: TestDataConfig


# Routes

@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status(
    db: AsyncSession = Depends(get_db),
):
    """
    Get demo environment status and statistics
    
    Returns:
    - Demo tenant info
    - Number of clients, invoices, transactions, GL entries
    - Last reset timestamp
    """
    try:
        service = DemoResetService(db)
        stats = await service.get_demo_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting demo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=DemoResetResponse, dependencies=[Depends(require_demo_mode)])
async def reset_demo_environment(
    db: AsyncSession = Depends(get_db),
):
    """
    Reset demo environment
    
    This will:
    - Delete all demo invoices (vendor and customer)
    - Delete all demo bank transactions
    - Delete all demo general ledger entries
    - Reset account balances to zero
    - Preserve clients and chart of accounts
    
    **Warning: This action cannot be undone!**
    """
    try:
        service = DemoResetService(db)
        result = await service.reset_demo_data()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resetting demo environment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-test", response_model=TestDataRunResponse, dependencies=[Depends(require_demo_mode)])
async def run_test_data_generation(
    config: TestDataConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate test data for demo environment
    
    This will create:
    - Supplier invoices (EHF XML format)
    - Bank transactions (CSV simulation)
    - Customer invoices (JSON)
    - Edge cases (high/low confidence, duplicates, unmatched)
    
    The generation runs in the background. Use the returned task_id to check progress.
    """
    try:
        from app.services.demo.test_data_generator import TestDataGeneratorService
        import uuid
        
        task_id = str(uuid.uuid4())
        
        # Create service
        service = TestDataGeneratorService(db)
        
        # Add background task
        background_tasks.add_task(
            service.generate_test_data,
            task_id=task_id,
            config=config.model_dump(),
        )
        
        logger.info(f"Started test data generation task: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": f"Test data generation started with {config.invoices_per_client} invoices per client",
            "config": config,
        }
        
    except Exception as e:
        logger.error(f"Error starting test data generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get status of test data generation task
    
    Returns:
    - Status: pending/running/completed/failed
    - Progress information
    - Results (when completed)
    """
    try:
        from app.services.demo.test_data_generator import TestDataGeneratorService
        
        service = TestDataGeneratorService(db)
        status = await service.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
