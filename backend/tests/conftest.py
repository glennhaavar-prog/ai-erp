"""
Pytest configuration and fixtures for Kontali ERP tests
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database import Base

# Import all models to ensure they're registered with SQLAlchemy Base
from app.models.client import Client
from app.models.tenant import Tenant
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine
from app.models.vendor_invoice import VendorInvoice
from app.models.vendor import Vendor
from app.models.chart_of_accounts import Account
from app.models.tax_code import TaxCode
from app.models.review_queue import ReviewQueue
from uuid import uuid4


# Test database URL (use same database with transaction isolation)
# TODO: Create separate test database when we have superuser access
TEST_DATABASE_URL = "postgresql+asyncpg://erp_user:erp_password@localhost:5432/ai_erp"


# Removed custom event_loop fixture - use pytest-asyncio default


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )
    
    # Note: Using existing database with transaction rollback for isolation
    # Tables already exist from migrations
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine):
    """Create database session for each test"""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_tenant(db_session):
    """Create a test tenant for tests"""
    # Use random org_number to avoid conflicts
    tenant = Tenant(
        id=uuid4(),
        name="Test Regnskapsbyrå",
        org_number=f"9876{uuid4().hex[:5]}"
    )
    db_session.add(tenant)
    await db_session.flush()
    return tenant


@pytest.fixture
async def test_client(db_session, test_tenant):
    """Create a test client for tests"""
    # Use random org_number to avoid conflicts
    client = Client(
        id=uuid4(),
        tenant_id=test_tenant.id,
        client_number=f"TEST{uuid4().hex[:6]}",
        name="Test AS",
        org_number=f"9998{uuid4().hex[:5]}",
        is_demo=True
    )
    db_session.add(client)
    await db_session.flush()
    return client
