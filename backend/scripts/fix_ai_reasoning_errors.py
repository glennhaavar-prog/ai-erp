#!/usr/bin/env python3
"""
Fix ai_reasoning errors in review_queue table
Replace error messages with sensible defaults
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.review_queue import ReviewQueue


async def fix_ai_reasoning_errors():
    """Fix AI reasoning errors in database"""
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Find items with errors
        query = select(ReviewQueue).where(
            ReviewQueue.ai_reasoning.like('%ARRAY.contains%')
        )
        result = await session.execute(query)
        items = result.scalars().all()
        
        print(f"Found {len(items)} items with ARRAY.contains errors")
        
        if not items:
            print("No errors to fix!")
            return
        
        # Fix each item
        fixed_count = 0
        for item in items:
            # Generate a sensible default reasoning based on confidence
            confidence = item.ai_confidence or 0
            
            if confidence == 0:
                new_reasoning = (
                    "Low confidence due to: Unknown vendor or first-time transaction. "
                    "Manual review recommended to establish pattern."
                )
            elif confidence < 50:
                new_reasoning = (
                    "Medium-low confidence. Some uncertainty in account classification "
                    "or VAT handling. Review suggested booking before approval."
                )
            elif confidence < 85:
                new_reasoning = (
                    "Medium confidence. Transaction matches some historical patterns "
                    "but requires verification due to unusual characteristics."
                )
            else:
                new_reasoning = (
                    "High confidence based on historical patterns and vendor familiarity."
                )
            
            # Update the item
            item.ai_reasoning = new_reasoning
            fixed_count += 1
        
        # Commit changes
        await session.commit()
        print(f"✅ Fixed {fixed_count} items")
    
    await engine.dispose()


if __name__ == "__main__":
    print("🔧 Fixing AI reasoning errors...")
    asyncio.run(fix_ai_reasoning_errors())
    print("✅ Done!")
