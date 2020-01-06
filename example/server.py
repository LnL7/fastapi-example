"""
Example REST API
"""
import asyncio
import logging
import sqlite3
from typing import Any, Dict, List

import example
from example.download import Fetcher
from example.models import Package, Token, database
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

DEFAULT_STATUS = 'created'

logger = logging.getLogger(__name__)

app = FastAPI(title="example", version=example.__version__)


@app.middleware('http')
async def add_server_version(request: Request, call_next):
    token = await Token.get_or_default(get_current_token(request))
    request
    if token:
        response = await call_next(request)
        return response
    else:
        return JSONResponse(status_code=401, content={
            'detail': 'authentication token required'
        })


def get_current_token(request: Request):
    _, _, token = request.headers.get('Authorization', '').partition('Token ')
    return token


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
    return await Package.all()


@app.get('/api/v1/package/{record_id}', response_model=Package)
async def retrieve_package(record_id: int) -> Dict[str, Any]:
    """
    Retrieve a package
    """
    return await Package.get(record_id)


async def download_task(record_id: int):
    pkg = await Package.get(record_id)
    await Fetcher.download(pkg.name, pkg.version)
    try:
        await Package.update_status(record_id, 'downloaded',
                                    from_status='created')
    except Exception as exc:
        logger.error('download failed: %s', exc)


@app.post('/api/v1/package/{record_id}/download', response_model=PackageStatus)
async def download_package(record_id: int, tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Schedule the download of a package
    """
    pkg = await Package.get(record_id)
    if pkg:
        if pkg.status == 'created':
            logger.info('scheduled task for %s', record_id)
            tasks.add_task(download_task, record_id)
        return {'status': pkg.status}
    else:
        raise HTTPException(404, detail="package does not exist")


@app.post('/api/v1/package/{record_id}/activate', response_model=PackageStatus)
async def activate_package(record_id: int) -> Dict[str, Any]:
    """
    Make a package active
    """
    pkg = await Package.get_with_status(record_id, 'downloaded')
    if pkg:
        await Package.update_status(record_id, 'activated', from_status='downladed')
        return {'status': 'activated'}
    raise HTTPException(412, detail="package does not exist or is still downloading")


@app.post('/api/v1/packages', response_model=Package)
async def create_package(pkg: CreatePackage) -> Dict[str, Any]:
    """
    List all packages
    """
    kwargs = dict(name=pkg.name, version=pkg.version, status=DEFAULT_STATUS)
    try:
        record_id = await Package.create(**kwargs)
        return {**kwargs, 'id': record_id}
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, detail=str(exc))


@app.get('/api/v1/tokens', response_model=List[Token])
async def list_tokens() -> Dict[str, Any]:
    """
    Generate a new authentication token
    """
    return await Token.all()


@app.post('/api/v1/tokens', response_model=Token)
async def create_token() -> Dict[str, Any]:
    """
    Generates a new authentication token
    """
    try:
        token = await Token.generate()
        return token
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, detail=str(exc))


@app.delete('/api/v1/tokens/all')
async def reset_all_tokens(token: str = Depends(get_current_token)) -> Dict[str, Any]:
    """
    Expires all tokens except for the one currently used
    """
    # Tokens should really be split up into root and api tokens.
    await Token.delete_all_except(token)
    return {}


@app.delete('/api/v1/token/{record_id}')
async def destroy_token(record_id: int) -> Dict[str, Any]:
    """
    Expires an authentication token
    """
    await Token.delete(record_id)
    return {}
