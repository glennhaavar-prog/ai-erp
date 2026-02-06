"""
Multi-Agent System for Kontali ERP

This module contains all AI agents that power the automated accounting system.

Architecture:
- Orchestrator: Coordinates all agents via database events
- Invoice Parser: Parses EHF XML invoices
- Bookkeeping: Creates journal entries with AI
- Learning: Learns patterns from accountant corrections

Communication:
All agents communicate via the database (agent_events and agent_tasks tables).
No direct agent-to-agent communication.

Usage:
    # Run orchestrator
    python -m app.agents.run_orchestrator
    
    # Run worker agents
    python -m app.agents.worker invoice_parser
    python -m app.agents.worker bookkeeper
    python -m app.agents.worker learning
"""

from app.agents.base import BaseAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.invoice_parser_agent import InvoiceParserAgent
from app.agents.bookkeeping_agent import BookkeepingAgent
from app.agents.learning_agent import LearningAgent
from app.agents.worker import AgentWorker, run_worker

__all__ = [
    "BaseAgent",
    "OrchestratorAgent",
    "InvoiceParserAgent",
    "BookkeepingAgent",
    "LearningAgent",
    "AgentWorker",
    "run_worker",
]
