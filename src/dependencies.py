import uuid

from fastapi.params import Depends
from pydantic.v1.schema import schema
from sqlalchemy import delete, update
from sqlalchemy.dialects.mssql.information_schema import sequences
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from typing import Annotated

from database import init_db
import models


SessionLocal, engine = init_db()


async def startup_events():
    pass


async def get_db() -> AsyncSession:
    db = SessionLocal()
    try:
        yield db
    finally:
        # print(db.identity_map)
        await db.close()


AsyncDB = Annotated[AsyncSession, Depends(get_db)]


async def get_product_id_offers(db: AsyncDB, id_: UUID) -> list[models.Offer] | None:
    sequence = (await db.execute(select(models.Offer).where(models.Offer.product_id == id_))).all()
    return [x[0] for x in sequence]


async def delete_product(db: AsyncDB, id_: UUID) -> UUID:
    statement = delete(models.Product).where(models.Product.id == id_)
    await db.execute(statement)
    await db.commit()
    return id_


async def create_product(db: AsyncDB, id_: UUID, name: str, description: str) -> models.Product:
    if id_ is None:
        # create a new uuid if not listed
        id_ = uuid.uuid4()

    product = models.Product(id=id_, name=name, description=description)
    db.add(product)
    await db.commit()
    return product


async def update_product(db: AsyncDB, id_: UUID, name: str, description: str) -> models.Product:
    statement = update(models.Product).where(models.Product.id == id_).values(name=name, description=description)\
        .returning(models.Product)
    result = await db.execute(statement)
    await db.commit()
    return result.scalars().first()


ProductOffers = Annotated[list[models.Offer], Depends(get_product_id_offers)]
DeleteProduct = Annotated[UUID, Depends(delete_product)]
CreateProduct = Annotated[models.Product, Depends(create_product)]


