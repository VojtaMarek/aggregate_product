import uuid
from contextlib import asynccontextmanager
from email.policy import default
from itertools import product
from typing import Optional

from fastapi import FastAPI, HTTPException
from uuid import UUID
import logging

import dependencies
import models

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await dependencies.startup_events()
    yield


app = FastAPI(
    lifespan=lifespan,
    docs_url='/docs'
)


@app.get("/")
async def version():
    return {"version": "0.1.0"}


@app.get("/product/{product_id}/offers")
async def get_product_id_offers(products: dependencies.ProductOffers):
    if products is None:
        raise HTTPException(status_code=404, detail='Product not in local database and may not be registered.')
    return products


@app.delete("/product/{id_}")
async def delete_product(id_: dependencies.DeleteProduct):
    return id_


@app.post("/product")
async def create_product(db: dependencies.AsyncDB,
                         id_: Optional[UUID] = None,
                         name: Optional[str] = None,
                         description: Optional[str] = None):
    _product: models.Product | None = await dependencies.create_product(db, id_, name, description)
    if not _product:
        raise HTTPException(status_code=404, detail='Product registration failed. Access token may not be gotten.')
    return _product


@app.patch("/product/{id_}")
async def update_product(db: dependencies.AsyncDB,
                         id_: UUID,
                         name: Optional[str] = None,
                         description: Optional[str] = None):
    _product: models.Product = await dependencies.update_product(db, id_, name, description)
    return _product


