import asyncio
import json
import os
import uuid
from datetime import datetime
from logging import getLogger

from fastapi.params import Depends
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from typing import Annotated

import service
import tools
from database import init_db
import models
from models import Offer

logger = getLogger(__name__)
SessionLocal, engine = init_db()


async def startup_events():
    # run background tasks
    loop = asyncio.get_event_loop()
    loop.create_task(run_periodic_tasks())


async def run_periodic_tasks():
    # periodically request for access token if not expired
    base_url = os.environ['BASE_URL'] + '/auth'
    service_manager = service.ServiceManager(base_url, os.getenv('REFRESH_TOKEN'), 'POST')
    access_token_diff: int = (datetime.now() - datetime.fromisoformat(tools.get_access_token(time=True))).seconds
    timeout = 5 * 60
    while True:
        if access_token_diff >= timeout:
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
                    tools.save_access_token(access_token)
                    logger.error(f'..access token valid from {datetime.now()}')
                await asyncio.sleep(5*60)
            except Exception as e:
                logger.error(f'Failed with periodic tasks running. Detail: {e}')
                raise
        else:
            await asyncio.sleep(1)


async def get_db() -> AsyncSession:
    db = SessionLocal()
    try:
        yield db
    finally:
        # print(db.identity_map)
        await db.close()


AsyncDB = Annotated[AsyncSession, Depends(get_db)]


async def get_products(db: AsyncDB) -> list[models.Product | None]:
    products = (await db.execute(select(models.Product))).all()
    return products

async def get_product_id_offers(db: AsyncDB, product_id: UUID) -> list[models.Offer] | None:
    # try to update offers for product
    try:
        product = (await db.execute(select(models.Product).where(models.Product.id == product_id))).scalar_one_or_none()
    except Exception as e:
        product = None
        logger.warning(f"Error: {e}")
    if product and product.id == product_id:

        # add offers form external service
        base_url = os.environ['BASE_URL'] + '/products/%s/offers' % product_id
        access_token = tools.get_access_token()[0]
        service_manager = service.ServiceManager(base_url, access_token, 'GET')
        res = await service_manager.async_request()
        if res.status_code == 200:
            for offer in json.loads(res.content):
                await add_offer(db, UUID(offer.get('id')), offer.get('price'), offer.get('items_in_stock'), product_id)
        elif res.status_code == 404:
            logger.warning("No offers found by the service for the given product.")

        # get all local db products with in stock
        try:
            offers_locally = (await db.execute(select(models.Offer).where(models.Offer.product_id == product_id,
                                                                          models.Offer.items_in_stock > 0))).all()
        except Exception as e:
            return e
        return [x[0] for x in offers_locally]
    return None


async def delete_product(db: AsyncDB, id_: UUID) -> UUID:
    statement = delete(models.Product).where(models.Product.id == id_)
    await db.execute(statement)
    await db.commit()
    return id_


async def create_product(db: AsyncDB, id_: UUID, name: str, description: str) -> tuple[models.Product | None, int]:
    if id_ is None:
        # create a new uuid if not listed
        id_ = uuid.uuid4()

    product = models.Product(id=id_, name=name, description=description)

    # register new product
    code = await register_product(product)
    res = None
    if code in {200, 201}:
        db.add(product)
        await db.commit()
        res = product
    return res, code


async def update_product(db: AsyncDB, id_: UUID, name: str, description: str) -> models.Product:
    # product = (await db.execute(select(models.Product).where(models.Product.id == id_))).scalar_one_or_none();   # .values(name=name or product.name, description=description or product.description)\
    statement = update(models.Product).where(models.Product.id == id_).values(name=name, description=description)\
        .returning(models.Product)
    result = await db.execute(statement)
    await db.commit()
    return result.scalars().first()


ProductOffers = Annotated[list[models.Offer] | None, Depends(get_product_id_offers)]
DeleteProduct = Annotated[UUID, Depends(delete_product)]
CreateProduct = Annotated[models.Product | int, Depends(create_product)]
Products = Annotated[list[models.Product | None], Depends(get_products)]


async def register_product(product: models.Product) -> int:
    """Return: True if registered, False otherwise."""
    base_url = os.environ['BASE_URL'] + '/products/register'
    access_token = tools.get_access_token()
    service_manager = service.ServiceManager(base_url, access_token, 'POST')
    product_dict = tools.to_dict(product)

    res = await service_manager.async_request(data=product_dict)
    return res.status_code or 404


async def add_offer(db: AsyncDB, id_: UUID, price: int, items_in_stock: int, product_id: UUID) -> None:
    offer_in_db = (await db.execute(select(Offer).where(Offer.id == id_))).scalar_one_or_none()
    if offer_in_db is None:
        offer = models.Offer(id=id_, price=price, items_in_stock=items_in_stock, product_id=product_id)
        db.add(offer)
        await db.commit()