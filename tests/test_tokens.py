import asyncio
import os
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'

import mock
from example.models import Token, initialize
from example.server import app
from starlette.testclient import TestClient

loop = asyncio.get_event_loop()

initialize(drop_all=True) # FIXME: do this before each test to prevent state?
client = TestClient(app)


TEST_TOKEN = 'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
TEST_HEADERS = {'Authorization': f'Token {TEST_TOKEN}'}


def test_no_tokens():
    response = client.get('/api/v1/tokens')
    assert response.status_code == 200
    assert response.json() == []


def test_create_token():
    response = client.post('/api/v1/tokens')
    assert response.status_code == 200
    assert response.json() == {'id': 1, 'token': mock.ANY}
    new_token = response.json()['token']
    new_headers = {'Authorization': f'Token {new_token}'}

    response = client.get('/api/v1/tokens')
    assert response.status_code == 401
    response = client.get('/api/v1/tokens', headers=new_headers)
    assert response.status_code == 200


def test_token_required():
    response = client.get('/api/v1/hello', headers=TEST_HEADERS)
    assert response.status_code == 401
    response = client.get('/api/v1/packages', headers=TEST_HEADERS)
    assert response.status_code == 401
    response = client.get('/api/v1/tokens', headers=TEST_HEADERS)
    assert response.status_code == 401


def test_replace_token():
    loop.run_until_complete(Token.replace_token(1, TEST_TOKEN))
    response = client.get('/api/v1/tokens', headers=TEST_HEADERS)
    assert response.status_code == 200


def test_revoke_token():
    response = client.post('/api/v1/tokens', headers=TEST_HEADERS)
    assert response.status_code == 200
    assert response.json() == {'id': 2, 'token': mock.ANY}
    new_token = response.json()['token']
    new_headers = {'Authorization': f'Token {new_token}'}

    response = client.get('/api/v1/tokens', headers=new_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.delete('/api/v1/token/2', headers=new_headers)
    assert response.status_code == 200
    response = client.get('/api/v1/tokens', headers=new_headers)
    assert response.status_code == 401
    response = client.get('/api/v1/tokens', headers=TEST_HEADERS)
    assert response.status_code == 200
    assert len(response.json()) == 1
