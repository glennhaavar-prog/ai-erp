"""
GraphQL Schema - Root Query and Mutation
"""
import strawberry
from typing import List, Optional
from app.graphql.types.client import Client


@strawberry.type
class Query:
    """Root Query"""
    
    @strawberry.field
    async def hello(self) -> str:
        """Test query"""
        return "Hello from AI-Agent ERP!"
    
    @strawberry.field
    async def clients(
        self,
        tenant_id: Optional[strawberry.ID] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Client]:
        """Get list of clients"""
        # TODO: Implement actual database query
        return []
    
    @strawberry.field
    async def client(self, id: strawberry.ID) -> Optional[Client]:
        """Get single client by ID"""
        # TODO: Implement actual database query
        return None


@strawberry.type
class Mutation:
    """Root Mutation"""
    
    @strawberry.field
    async def ping(self) -> str:
        """Test mutation"""
        return "pong"


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
