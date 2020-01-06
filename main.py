"""
Example REST API
"""
import logging
import os
from typing import Any, Dict, List

import databases
import example
import sqlalchemy
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./example.db')
DEFAULT_STATUS = 'created'

logger = logging.getLogger(__name__)

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
engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

app = FastAPI()


class Package(BaseModel):
    id: int
    name: str
    version: str
    status: str


class CreatePackage(BaseModel):
    name: str
    version: str


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get('/hello')
async def hello() -> Dict[str, Any]:
    """
    Returns a familiar, friendly greeting
    """
    return {'message': 'Hello World!'}


@app.get('/api/v1/version')
async def version() -> Dict[str, Any]:
    """
    Returns the version of the example server
    """
    return {'version': example.__version__}


@app.get('/api/v1/packages', response_model=List[Package])
async def list_packages() -> Dict[str, Any]:
    """
    List all packages
    """
    query = packages.select()
    return await database.fetch_all(query)


async def download_package(record_id):
    query = packages.select().where(packages.c.id == record_id)
    pkg = await database.fetch_one(query)
    logger.info(f'downloading {pkg.name}~{pkg.version}...')
    logger.warning('not implemented')  # WIP
    query = packages.update().where(packages.c.id == record_id).values(status='downloaded')
    await database.execute(query)



@app.post('/api/v1/packages', response_model=Package)
async def create_package(pkg: CreatePackage, tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    List all packages
    """
    kwargs = dict(name=pkg.name, version=pkg.version, status=DEFAULT_STATUS)
    query = packages.insert().values(**kwargs)
    record_id = await database.execute(query)
    tasks.add_task(download_package, record_id)
    return {**kwargs, 'id': record_id}
