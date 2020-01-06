import os
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'

from example.models import initialize
from example.server import app
from starlette.testclient import TestClient


initialize(drop_all=True)
client = TestClient(app)


def test_hello():
    response = client.get('/hello')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello World!'}
