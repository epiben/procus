import sys

from app_fastapi import app
from fastapi.testclient import TestClient
from utils.db import (
    make_engine,
    make_engine_test,
)

sys.path.insert(0, "/app")

client = TestClient(app)
app.dependency_overrides[make_engine] = make_engine_test


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
