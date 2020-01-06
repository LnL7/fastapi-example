"""
Example REST API
"""
import logging
from typing import Any, Dict

import example
from fastapi import FastAPI

logger = logging.getLogger(__name__)

app = FastAPI()


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
