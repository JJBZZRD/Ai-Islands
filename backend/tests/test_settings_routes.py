import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
import json

client = TestClient(app)

def mask_api_key(data):
    if isinstance(data, dict):
        return {k: mask_api_key(v) if k == "api_key" else v for k, v in data.items()}
    elif isinstance(data, str) and len(data) > 10:
        return '*' * (len(data) - 4) + data[-4:]
    else:
        return data

@pytest.mark.order1
def test_update_watson_settings():
    endpoint = "/settings/update-watson-settings"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(endpoint, json={
        "api_key": "sAXfvscbVW_21CY0lQ1GjfW5c3dqVVQ_ae97GEEag7oq",
        "project_id": "e55a3b58-0711-4438-8909-0e36cc1d617b",
        "location": "eu-gb"
    })
    assert response.status_code == 200
    print(f"Response: {response.json()}")

@pytest.mark.order2
def test_get_watson_settings():
    endpoint = "/settings/get-watson-settings"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(endpoint)
    assert response.status_code == 200
    settings = response.json()
    
    print("Watson Settings:")
    print(json.dumps(mask_api_key(settings), indent=2))
    
    assert "api_key" in settings
    assert "location" in settings
    assert "project" in settings

@pytest.mark.order3
def test_update_chunking_settings():
    endpoint = "/settings/update-chunking-settings"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(endpoint, json={
        "use_chunking": False,
        "chunk_size": 1000,
        "chunk_overlap": 100,
        "chunk_method": "csv_row",
        "rows_per_chunk": 1,
        "csv_columns": []
    })
    assert response.status_code == 200
    print(f"Response: {response.json()}")

@pytest.mark.order4
def test_get_chunking_settings():
    endpoint = "/settings/get-chunking-settings"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(endpoint)
    assert response.status_code == 200
    print("Chunking Settings:")
    print(json.dumps(response.json(), indent=2))

@pytest.mark.order5
def test_set_hardware():
    endpoint = "/settings/set-hardware"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(endpoint, json={"device": "cpu"})
    assert response.status_code == 200
    print(f"Response: {response.json()}")

@pytest.mark.order6
def test_get_hardware():
    endpoint = "/settings/get-hardware"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(endpoint)
    assert response.status_code == 200
    print(f"Response: {response.json()}")

@pytest.mark.order7
def test_check_gpu():
    endpoint = "/settings/check-gpu"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(endpoint)
    assert response.status_code == 200
    print(f"Response: {response.json()}")