"""
Example REST API
"""
import asyncio
import logging
import os
import sqlite3
from typing import Any, Dict, List

import databases
import example
import sqlalchemy
from fastapi import BackgroundTasks, FastAPI, HTTPException
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

app = FastAPI(title="example", version=example.__version__)


class Package(BaseModel):
    id: int
    name: str
    version: str
    status: str


class CreatePackage(BaseModel):
    name: str
    version: str


class PackageStatus(BaseModel):
    status: str


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


@app.get('/api/v1/package/{record_id}', response_model=Package)
async def retrieve_package(record_id: int) -> Dict[str, Any]:
    """
    Retrieve a package
    """
    query = packages.select().where(packages.c.id == record_id)
    return await database.fetch_one(query)


@app.post('/api/v1/package/{record_id}/activate', response_model=PackageStatus)
async def activate_package(record_id: int) -> Dict[str, Any]:
    """
    Make a package active
    """
    query = packages.select().where(packages.c.id == record_id \
                                    and packages.c.status == 'downloaded')
    pkg = await database.fetch_one(query)
    if pkg:
        return {'status': 'activated'}
    else:
        raise HTTPException(412, detail="package does not exist or is still downloading")


async def download_package(record_id: int):
    query = packages.select().where(packages.c.id == record_id)
    pkg = await database.fetch_one(query)
    logger.info(f'downloading {pkg.name}~{pkg.version}...')
    logger.warning('not implemented')  # WIP
    await asyncio.sleep(60)
    query = packages.update().where(packages.c.id == record_id).values(status='downloaded')
    await database.execute(query)



@app.post('/api/v1/packages', response_model=Package)
async def create_package(pkg: CreatePackage, tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    List all packages
    """
    kwargs = dict(name=pkg.name, version=pkg.version, status=DEFAULT_STATUS)
    query = packages.insert().values(**kwargs)
    try:
        record_id = await database.execute(query)
        tasks.add_task(download_package, record_id)
        return {**kwargs, 'id': record_id}
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
