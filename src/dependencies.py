import asyncio
import os
import uuid
from logging import getLogger

from fastapi.params import Depends
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from typing import Annotated

import service
from database import init_db
import models


logger = getLogger(__name__)
SessionLocal, engine = init_db()


async def startup_events():
    # run background tasks
    loop = asyncio.get_event_loop()
    loop.create_task(run_periodic_tasks())


async def run_periodic_tasks():
    # periodically request for access token
    base_url = os.getenv('BASE_URL') + '/auth'
    service_manager = service.ServiceManager(base_url, os.getenv('REFRESH_TOKEN'), 'POST')
    while True:
        try:
            logger.warning('Attempt to get access token..')
            res = await service_manager.async_request()
            # res = service_manager.request()

            # inner loop to repeat request when 400 until 201
            timer = 1
            while res.status_code != 201 and res.status_code == 400:
                logger.warning(f'Repeating attempt to get access token after {timer}s')
                await asyncio.sleep(timer)
                res = await service_manager.async_request()
                # res = service_manager.request()
                timer *= 2

            if access_token := res.json().get('access_token', False):
                os.environ['ACCESS_TOKEN'] = access_token
            await asyncio.sleep(5*60)
        except Exception as e:
            logger.error(f'Failed with periodic tasks running. Detail: {e}')
            raise


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


