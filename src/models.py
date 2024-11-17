from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()


class Product(Base):
    __tablename__ = 'products'

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)


class Offer(Base):
    __tablename__ = 'offers'

    id = Column(UUID, primary_key=True)
    price = Column(Integer, nullable=True)
    items_in_stock = Column(Integer, nullable=True)
    product_id = Column(UUID, ForeignKey('products.id'))
