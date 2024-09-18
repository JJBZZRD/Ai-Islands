# import pytest
# import json
# from fastapi.testclient import TestClient
# from backend.api.main import app
# from pathlib import Path

# client = TestClient(app)

# def test_upload_dataset():
#     local_dataset_path = r"C:\Users\costa\OneDrive\Desktop\DataTest_AI_Islands\fictional_space_colonies.csv"
#     response = client.post(f"/data/upload_dataset/?file_path={local_dataset_path}")
    
#     print("\nUpload Dataset Response:")
#     print(json.dumps(response.json(), indent=2))
    
#     assert response.status_code == 200
#     assert "message" in response.json()

#     dataset_name = Path(local_dataset_path).stem
#     expected_path = Path(f"Datasets/{dataset_name}/{dataset_name}.csv")
#     assert expected_path.exists()

# def test_process_dataset():
#     response = client.post("/data/process_dataset", json={
#         "file_path": "Datasets/fictional_space_colonies/fictional_space_colonies.csv",
#         "model_name": "msmarco-distilbert-base-v4"
#     })
    
#     print("\nProcess Dataset Response:")
#     print(json.dumps(response.json(), indent=2))
    
#     assert response.status_code == 200

# def test_list_datasets():
#     response = client.get("/data/list_datasets")
    
#     print("\nList Datasets Response:")
#     print(json.dumps(response.json(), indent=2))
    
#     assert response.status_code == 200

# def test_get_available_models():
#     response = client.get("/data/available_models")
    
#     print("\nAvailable Models Response:")
#     print(json.dumps(response.json(), indent=2))
    
#     assert response.status_code == 200