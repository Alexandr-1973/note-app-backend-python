from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.conf.config import DB_URL

engine = create_async_engine(DB_URL)

SessionLocal = async_sessionmaker(bind=engine, autocommit=False, autoflush=False)

async def get_db():
    async with SessionLocal() as session:
        yield session