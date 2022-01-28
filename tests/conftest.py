# pytest 6.2.5
# https://pytest-flask.readthedocs.io/en/latest/
# pytest tests/conftest.py (-m, --verbose)

from main import app
import pytest

@pytest.mark.testIndex
def testIndex():
    client = app.test_client().get('/')
    assert client.status_code == 200
    assert client.get_data() 

@pytest.mark.testAuthToken    
def testAuthToken():
    client = app.test_client().get('/callback')
    assert client.status_code == 200

@pytest.mark.testUserPage
def testUserPage():
    client = app.test_client().get('/user')
    
    
