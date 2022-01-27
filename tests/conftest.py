# pytest 6.2.5
# https://pytest-flask.readthedocs.io/en/latest/
from main import app as flask_app
import pytest

@pytest.fixture
def app():
    yield flask_app
    
@pytest.fixture
def client(app):
    return app.test_client()

def testIndex(client):
    res = client.get('/') 
    assert res.status_code == 200 
 

