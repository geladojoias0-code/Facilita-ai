import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "changeme"}

def test_dashboard():
    res = client.get("/dashboard", headers=HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert 'total' in data
