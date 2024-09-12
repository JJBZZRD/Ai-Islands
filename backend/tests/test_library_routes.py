import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_download_model(model_id):
    response = client.post(f"/model/download-model?model_id={model_id}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Model {model_id} downloaded successfully"

def test_get_library():
    response = client.get("/library/get-full-library")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_get_model_info(model_id):
    response = client.get(f"/library/get-model-info-library?model_id={model_id}")
    assert response.status_code == 200
    model_info = response.json()
    assert "base_model" in model_info.keys()
    assert model_info["base_model"] == model_id

# def test_save_new_model():
#     response = client.post("/library/save_new_model", json={
#         "model_id": "base_model",
#         "new_model_id": "new_model",
#         "new_config": {"param1": "value1"}
#     })
#     assert response.status_code == 200
#     assert response.json() == {"message": "New model new_model saved successfully"}

# @pytest.mark.order4
# def test_update_model_id():
#     response = client.post("/library/update_model_id", json={
#         "model_id": "old_model",
#         "new_model_id": "updated_model"
#     })
#     assert response.status_code == 200
#     assert response.json() == {"message": "Model ID updated from old_model to updated_model"}