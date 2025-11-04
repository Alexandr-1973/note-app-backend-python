from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from src.conf.config import config

engine = create_async_engine(config.DB_URL)

SessionLocal = async_sessionmaker(bind=engine, autocommit=False, autoflush=False)

async def get_db():
    async with SessionLocal() as session:
        yield session