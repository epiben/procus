from fastapi.testclient import TestClient
import sys
sys.path.insert(0, "/app")
from utils.db import get_prod_db, get_test_db

from app_fastapi import app

client = TestClient(app)
app.dependency_overrides[get_prod_db] = get_test_db


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_read_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Service is healthy"}

def test_read_aquaicu():
    response = client.get("/aquaicu/Restart")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml; charset=utf-8"
    assert response.text == "<response>Invalid token</response>"



