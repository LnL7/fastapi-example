import os
from typing import List

import databases
import sqlalchemy
from pydantic import BaseModel

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./example.db')

metadata = sqlalchemy.MetaData()
packages = sqlalchemy.Table(
    'packages',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('name', sqlalchemy.String, nullable=False),
    sqlalchemy.Column('version', sqlalchemy.String, nullable=False),
    sqlalchemy.Column('status', sqlalchemy.String, nullable=False),

    sqlalchemy.UniqueConstraint('name', 'version'),
)

database = databases.Database(DATABASE_URL)


class Package(BaseModel):
    id: int
    name: str
    version: str
    status: str

    @classmethod
    def all(cls):
        query = packages.select()
        return database.fetch_all(query)

    @classmethod
    def get(cls, record_id: int):
        query = packages.select().where(packages.c.id == record_id)
        return database.fetch_one(query)

    @classmethod
    def create(cls, **kwargs):
        query = packages.insert().values(**kwargs)
        return database.execute(query)

    @classmethod
    def get_with_status(cls, record_id: int, status: str):
        query = packages.select().where(packages.c.id == record_id and \
                                        packages.c.status == status)
        return database.fetch_one(query)

    @classmethod
    def update_one(cls, record_id: int, **kwargs):
        query = packages.update().where(packages.c.id == record_id).values(**kwargs)
        return database.execute(query)

    @classmethod
    def update_status(cls, record_id, new_status, from_status=None):
        filters = packages.c.id == record_id
        if from_status:
            filters = filters and packages.c.status == from_status
        query = packages.update().where(filters).values(status=new_status)
        return database.execute(query)


def initialize(drop_all=False):
    engine = sqlalchemy.create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    if drop_all:
        metadata.drop_all(engine)
    metadata.create_all(engine)
