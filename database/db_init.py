from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base

async def init_db():
    engine = create_async_engine('sqlite+aiosqlite:///sociomind.db')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)