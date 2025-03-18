# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the SEC Filing Scanner API"}

def test_status():
    response = client.get("/filings/status")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.get("status") == "SEC Filing Scanner is running"
