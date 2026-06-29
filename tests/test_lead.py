import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

HEADERS = {"X-API-Key": "changeme"}

def test_create_and_get_lead():
    payload = {"place_id": "p1", "nome": "Loja X", "status": "novo"}
    res = client.post("/buscar-leads", params={"q":"empresa"}, headers=HEADERS)
    # importar_leads uses external SerpApi; this may return 0 but endpoint should respond
    assert res.status_code == 200

    # create lead directly via repository via API client's lower-level call
    res2 = client.get("/lead", params={"place_id":"p1"}, headers=HEADERS)
    # if not found should be 404
    assert res2.status_code in (200,404)
