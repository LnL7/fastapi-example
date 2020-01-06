import hashlib
import logging
import os
from typing import List

import databases
import sqlalchemy
from pydantic import BaseModel

logger = logging.getLogger(__name__)

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

tokens = sqlalchemy.Table(
    'tokens',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('token', sqlalchemy.String, nullable=False),

    sqlalchemy.UniqueConstraint('token'),
)

sqlalchemy.Index('idx_token', tokens.c.token)

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

class Token(BaseModel):
    id: int
    token: str

    @classmethod
    def all(cls):
        query = tokens.select()
        return database.fetch_all(query)

    @classmethod
    async def get_or_default(cls, token):
        query = tokens.count()
        count = await database.fetch_val(query)
        if count > 0:
            logger.info('validating token %s', token)
            query = tokens.select().where(tokens.c.token == token)
            return await database.fetch_one(query)
        else:
            return {'token': 'no_tokens_active'}

    @classmethod
    def replace_token(cls, record_id, token):
        query = tokens.update().where(tokens.c.id == record_id).values(token=token)
        return database.execute(query)

    @classmethod
    async def generate(cls):
        digest = hashlib.md5()
        digest.update(os.urandom(16))
        token = digest.hexdigest()
        query = tokens.insert().values(token=token)
        record_id = await database.execute(query)
        return {'id': record_id, 'token': token}

    @classmethod
    def delete_all_except(cls, token):
        query = tokens.delete().where(tokens.c.token != token)
        return database.execute(query)

    @classmethod
    def delete(cls, record_id):
        query = tokens.delete().where(tokens.c.id == record_id)
        return database.execute(query)



def initialize(drop_all=False):
    engine = sqlalchemy.create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    if drop_all:
        metadata.drop_all(engine)
    metadata.create_all(engine)
