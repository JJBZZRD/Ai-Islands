import pytest
import json
from fastapi.testclient import TestClient
from backend.api.main import app
from pathlib import Path

client = TestClient(app)

@pytest.mark.order1
def test_upload_dataset():
    endpoint = "/data/upload-dataset"
    local_dataset_path = r"C:\Users\costa\OneDrive\Desktop\DataTest_AI_Islands\fictional_space_colonies.csv"
    print(f"\nTesting endpoint: {endpoint}")
    
    # Create the request payload
    payload = {
        "file_path": local_dataset_path
    }
    
    response = client.post(endpoint, json=payload)
    
    # print("Upload Dataset Response:")
    # print(json.dumps(response.json(), indent=2))
    
    assert response.status_code == 200
    assert "message" in response.json()

    dataset_name = Path(local_dataset_path).stem
    expected_path = Path(f"Datasets/{dataset_name}/{dataset_name}.csv")
    assert expected_path.exists()

@pytest.mark.order2
def test_process_dataset():
    endpoint = "/data/process-dataset"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(endpoint, json={
        "file_path": "Datasets/fictional_space_colonies/fictional_space_colonies.csv",
        "model_name": "msmarco-distilbert-base-v4"
    })
    
    # print("Process Dataset Response:")
    # print(json.dumps(response.json(), indent=2))
    
    assert response.status_code == 200

@pytest.mark.order3
def test_dataset_processing_status():
    endpoint = "/data/dataset-processing-status"
    dataset_name = "fictional_space_colonies"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(f"{endpoint}?dataset_name={dataset_name}")
    
    # print("Dataset Processing Status Response:")
    # print(json.dumps(response.json(), indent=2))
    
    assert response.status_code == 200

@pytest.mark.order4
def test_dataset_processing_info():
    endpoint = "/data/dataset-processing-info"
    dataset_name = "fictional_space_colonies"
    processing_type = "default"  # Adjust this based on your actual processing types
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(f"{endpoint}?dataset_name={dataset_name}&processing_type={processing_type}")
    
    # print("Dataset Processing Info Response:")
    # print(json.dumps(response.json(), indent=2))
    
    assert response.status_code in [200, 404]  # Accept either 200 or 404
    if response.status_code == 200:
        assert "model_type" in response.json()
    else:
        assert "detail" in response.json()

@pytest.mark.order5
def test_datasets_processing_existence():
    endpoint = "/data/datasets-processing-existence"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(endpoint)
    
    # print("Datasets Processing Existence Response:")
    # print(json.dumps(response.json(), indent=2))
    
    assert response.status_code == 200

@pytest.mark.order6
def test_list_datasets():
    endpoint = "/data/list-datasets"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(endpoint)
    
    # print("List Datasets Response:")
    # print(json.dumps(response.json(), indent=2))
    
    assert response.status_code == 200

@pytest.mark.order7
def test_get_available_models():
    endpoint = "/data/available-models"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(endpoint)
    
    # print("Available Models Response:")
    # print(json.dumps(response.json(), indent=2))
    
    assert response.status_code == 200