# pytest 6.2.5
# https://pytest-flask.readthedocs.io/en/latest/
# pytest tests/conftest.py (-m, --verbose)

import json
from unittest import mock
import main 
import pytest

app = main.app

@pytest.mark.testIndex
def testIndex():
    client = app.test_client().get('/')
    assert client.status_code == 200
    html = client.data.decode()
    assert 'Login with Spotify' in html 

@pytest.mark.testAuthToken    
def testAuthToken():
    client = app.test_client().get('/callback')
    assert client.status_code == 200

@pytest.mark.testUserPage
def testUserPage():
    client = app.test_client().get(
        '/user',
        content_type = 'application/json',
        Authorization = 'mock_access_token_1234',
    )
    data = json.loads(client.get_data(as_text=True))
    assert data
    
    