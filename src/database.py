from typing import Tuple
import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, create_async_engine
import os


database_url = os.getenv('DATABASE_URL')


def init_db() -> Tuple[async_sessionmaker, AsyncEngine]:
    engine = create_async_engine(database_url)
    return async_sessionmaker(engine, expire_on_commit=False), engine