import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
import json

client = TestClient(app)

@pytest.mark.order1
def test_update_watson_settings():
    response = client.post("/settings/update_watson_settings", json={
        "api_key": "obx21Ap0YYotQMDyEctsKOFgA23_rcDH9hBszrFlFHR_",
        "project_id": "a01f5d35-7117-4c78-9ddd-d2b4006e622e",
        "location": "eu-gb"
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Watson settings updated successfully"}

@pytest.mark.order2
def test_get_watson_settings():
    response = client.get("/settings/get_watson_settings")
    assert response.status_code == 200
    settings = response.json()
    
    print("\nWatson Settings:")
    print(json.dumps(settings, indent=2))
    
    assert "api_key" in settings
    assert "location" in settings
    assert "project" in settings

@pytest.mark.order3
def test_update_chunking_settings():
    response = client.post("/settings/update_chunking_settings", json={
        "use_chunking": False,
        "chunk_size": 1000,
        "chunk_overlap": 100,
        "chunk_method": "csv_row",
        "rows_per_chunk": 1,
        "csv_columns": []
    })
    assert response.status_code == 200
    assert response.json() == {"message": "Chunking settings updated successfully"}

@pytest.mark.order4
def test_get_chunking_settings():
    response = client.get("/settings/get_chunking_settings")
    assert response.status_code == 200
    print("\nChunking Settings:")
    print(json.dumps(response.json(), indent=2))

@pytest.mark.order5
def test_set_hardware():
    response = client.post("/settings/set-hardware", json={"device": "cpu"})
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully set hardware to cpu"}
    print(response.json())

@pytest.mark.order6
def test_get_hardware():
    response = client.get("/settings/get-hardware")
    assert response.status_code == 200
    assert response.json() == {"hardware": "cpu"}
    print(response.json())

@pytest.mark.order7
def test_check_gpu():
    response = client.get("/settings/check-gpu")
    assert response.status_code == 200
    assert "CUDA available" in response.json()
    print(response.json())