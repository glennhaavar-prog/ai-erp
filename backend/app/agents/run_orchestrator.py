"""
Run Orchestrator - Start the orchestrator agent event loop
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.agents.orchestrator import OrchestratorAgent

logger = logging.getLogger(__name__)


async def run_orchestrator(db_url: str = None):
    """
    Run the orchestrator agent
    
    Args:
        db_url: Database URL (defaults to settings.DATABASE_URL)
    """
    # Create database session factory
    db_url = db_url or settings.DATABASE_URL
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create orchestrator
    orchestrator = OrchestratorAgent()
    
    logger.info("Starting Orchestrator Agent")
    
    try:
        async with async_session() as db:
            await orchestrator.run(db)
    except KeyboardInterrupt:
        logger.info("Orchestrator: Received interrupt signal")
        orchestrator.stop()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run orchestrator
    asyncio.run(run_orchestrator())
