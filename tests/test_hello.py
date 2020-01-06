import os
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'

import mock
import sqlalchemy
from example import server
from fastapi import FastAPI
from starlette.testclient import TestClient

engine = sqlalchemy.create_engine(
    server.DATABASE_URL, connect_args={"check_same_thread": False}
)

server.metadata.drop_all(engine)  # FIXME: do this before each test to prevent state?
server.metadata.create_all(engine)
client = TestClient(server.app)


def test_hello():
    response = client.get('/hello')
    assert response.status_code == 200
    assert response.json() == {'message': 'Hello World!'}


def test_no_packages():
    response = client.get('/api/v1/packages')
    assert response.status_code == 200
    assert response.json() == []


def test_create_package():
    with mock.patch.object(server, 'download_package', return_value=None) as task:
        response = client.post('/api/v1/packages', data='{"name":"hello","version":"2.10"}')
        assert task.called

    assert response.status_code == 200
    assert response.json()['id'] == 1
    assert response.json()['status'] == 'created'


def test_list_packages():
    response = client.get('/api/v1/packages')
    assert response.status_code == 200
    assert response.json() == [
        {'id': 1, 'name': 'hello', 'version': '2.10', 'status': 'created'}
    ]

def test_retrieve_packages():
    response = client.get('/api/v1/package/1')
    assert response.status_code == 200
    assert response.json() == {
        'id': 1, 'name': 'hello', 'version': '2.10', 'status': 'created'
    }
