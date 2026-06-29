import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
HEADERS = {"X-API-Key": "changeme"}

def test_conversa_endpoints():
    payload = {"place_id":"p_test","autor":"user","texto":"ola"}
    res = client.post("/conversa", json=payload, headers=HEADERS)
    assert res.status_code == 200
    res2 = client.get(f"/conversa/p_test", headers=HEADERS)
    assert res2.status_code == 200
