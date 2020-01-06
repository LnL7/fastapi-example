import asyncio
import os
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'

import mock
import example
from example.models import Package, initialize
from example.server import app
from starlette.testclient import TestClient

loop = asyncio.get_event_loop()

initialize(drop_all=True) # FIXME: do this before each test to prevent state?
client = TestClient(app)


def test_no_packages():
    response = client.get('/api/v1/packages')
    assert response.status_code == 200
    assert response.json() == []


def test_create_package():
    response = client.post('/api/v1/packages', data='{"name":"hello","version":"2.10"}')
    assert response.status_code == 200
    assert response.json()['id'] == 1
    assert response.json()['status'] == 'created'


def test_list_packages():
    response = client.get('/api/v1/packages')
    assert response.status_code == 200
    assert response.json() == [
        {'id': 1, 'name': 'hello', 'version': '2.10', 'status': 'created'}
    ]

def test_retrieve_package():
    response = client.get('/api/v1/package/1')
    assert response.status_code == 200
    assert response.json() == {
        'id': 1, 'name': 'hello', 'version': '2.10', 'status': 'created'
    }


def test_download_package():
    with mock.patch.object(example.server, 'download_task', return_value=None) as task:
        response = client.post('/api/v1/package/1/download')
    assert response.status_code == 200
    assert response.json()['status'] == 'created'
    assert task.called


def test_download_package_doesnt_redownload():
    loop.run_until_complete(
        Package.update_one(1, status='downloaded')
    ) # TODO: async tests
    with mock.patch.object(example.server, 'download_task', return_value=None) as task:
        response = client.post('/api/v1/package/1/download')
    assert response.status_code == 200
    assert response.json()['status'] == 'downloaded'
    assert not task.called


def test_activate_package():
    response = client.post('/api/v1/package/1/activate')
    assert response.status_code == 200
    assert response.json() == {'status': 'activated'}


def test_activate_package_multiple_times():
    response = client.post('/api/v1/package/1/activate')
    assert response.status_code == 200
    assert response.json() == {'status': 'activated'}
