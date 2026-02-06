"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db, close_db
from app.graphql.schema import schema
from app.api.webhooks import ehf
from app.api import chat
from app.api.routes import review_queue, dashboard, reports, documents, accounts, audit, bank, customer_invoices

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting AI-Agent ERP...")
    await init_db()
    logger.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down AI-Agent ERP...")
    await close_db()
    logger.info("✅ Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Agent-first ERP system for Norwegian accounting firms",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GraphQL endpoint
graphql_app = GraphQLRouter(
    schema,
    graphiql=settings.DEBUG,  # GraphiQL UI in development only
)
app.include_router(graphql_app, prefix="/graphql")

# Webhooks
app.include_router(ehf.router)

# Chat API (with database integration)
app.include_router(chat.router)

# Review Queue REST API (for frontend)
app.include_router(review_queue.router)

# Trust Dashboard API
app.include_router(dashboard.router)

# Reports API (Hovedbok and other reports)
app.include_router(reports.router)

# Documents API (PDF retrieval)
app.include_router(documents.router)

# Accounts API (Chart of Accounts management)
app.include_router(accounts.router)

# Audit Trail API (System event history)
app.include_router(audit.router)

# Bank Reconciliation API (Upload and match transactions)
app.include_router(bank.router)

# Customer Invoice API (Outgoing/sales invoices)
app.include_router(customer_invoices.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI-Agent ERP API",
        "version": settings.APP_VERSION,
        "endpoints": {
            "graphql": "/graphql",
            "health": "/health",
            "chat": "/api/chat",
            "chat_docs": "/docs#/Chat",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
