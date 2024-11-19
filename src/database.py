from typing import Tuple
import asyncpg
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, create_async_engine

import os
from alembic import command

from models import Base


database_url = os.environ['DATABASE_URL']
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set!")

database_url_alembic = database_url.replace("+asyncpg", "")

alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", database_url_alembic)


def init_db() -> Tuple[async_sessionmaker, AsyncEngine]:
    engine = create_async_engine(database_url)
    return async_sessionmaker(engine, expire_on_commit=False), engine


def main():
    # create db from models
    engine = create_engine(database_url_alembic)
    Base.metadata.create_all(engine)
    command.upgrade(alembic_cfg, "head")

if __name__ == '__manin__':
    main()