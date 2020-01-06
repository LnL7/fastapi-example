import example.server
from fastapi import FastAPI
from starlette.testclient import TestClient

client = TestClient(example.server.app)


def test_hello():
    response = client.get('/hello')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello World!'}
