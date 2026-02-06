"""
Agent Worker - Generic worker that executes agent tasks
"""
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.agents.base import BaseAgent
from app.agents.invoice_parser_agent import InvoiceParserAgent
from app.agents.bookkeeping_agent import BookkeepingAgent
from app.agents.learning_agent import LearningAgent

logger = logging.getLogger(__name__)


class AgentWorker:
    """
    Generic agent worker
    
    Continuously polls for tasks and executes them using the appropriate agent.
    """
    
    def __init__(
        self,
        agent: BaseAgent,
        db_session_factory,
        polling_interval: int = 5
    ):
        """
        Initialize worker
        
        Args:
            agent: Agent instance to use for execution
            db_session_factory: SQLAlchemy session factory
            polling_interval: Seconds between polls (default 5)
        """
        self.agent = agent
        self.db_session_factory = db_session_factory
        self.polling_interval = polling_interval
        self.running = False
    
    async def run(self):
        """
        Main worker loop
        
        Continuously polls for tasks and executes them.
        """
        self.running = True
        logger.info(f"{self.agent.agent_type} worker: Starting")
        
        while self.running:
            try:
                async with self.db_session_factory() as db:
                    # Claim next task
                    task = await self.agent.claim_next_task(db)
                    
                    if task:
                        try:
                            # Execute task
                            logger.info(
                                f"{self.agent.agent_type} worker: "
                                f"Executing task {task.id} (type={task.task_type})"
                            )
                            
                            result = await self.agent.execute_task(db, task)
                            
                            # Complete task
                            await self.agent.complete_task(
                                db, str(task.id), result
                            )
                            
                            logger.info(
                                f"{self.agent.agent_type} worker: "
                                f"Completed task {task.id}"
                            )
                            
                        except Exception as e:
                            # Fail task
                            logger.error(
                                f"{self.agent.agent_type} worker: "
                                f"Task {task.id} failed: {str(e)}",
                                exc_info=True
                            )
                            
                            await self.agent.fail_task(
                                db, str(task.id), str(e), retry=True
                            )
                    
                    else:
                        # No tasks available, sleep
                        await asyncio.sleep(self.polling_interval)
            
            except Exception as e:
                logger.error(
                    f"{self.agent.agent_type} worker: "
                    f"Error in worker loop: {str(e)}",
                    exc_info=True
                )
                await asyncio.sleep(5)  # Brief pause before retry
    
    def stop(self):
        """Stop the worker"""
        logger.info(f"{self.agent.agent_type} worker: Stopping")
        self.running = False


async def run_worker(agent_type: str, db_url: Optional[str] = None):
    """
    Run a single agent worker
    
    Args:
        agent_type: Type of agent to run
        db_url: Database URL (defaults to settings.DATABASE_URL)
    """
    # Create agent
    agents = {
        "invoice_parser": InvoiceParserAgent(),
        "bookkeeper": BookkeepingAgent(),
        "learning": LearningAgent(),
    }
    
    agent = agents.get(agent_type)
    
    if not agent:
        raise ValueError(
            f"Unknown agent type: {agent_type}. "
            f"Available: {', '.join(agents.keys())}"
        )
    
    # Create database session factory
    db_url = db_url or settings.DATABASE_URL
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create and run worker
    worker = AgentWorker(agent, async_session)
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info(f"{agent_type} worker: Received interrupt signal")
        worker.stop()


if __name__ == "__main__":
    import sys
    
    # Get agent type from command line
    if len(sys.argv) < 2:
        print("Usage: python -m app.agents.worker <agent_type>")
        print("Available types: invoice_parser, bookkeeper, learning")
        sys.exit(1)
    
    agent_type = sys.argv[1]
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run worker
    asyncio.run(run_worker(agent_type))
