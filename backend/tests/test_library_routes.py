import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

@pytest.mark.order1
def test_get_library():
    response = client.get("/library")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.order2
def test_get_model_info():
    response = client.get("/library/model_info?model_id=ibm/granite-13b-chat-v2")
    assert response.status_code == 200
    assert "model_id" in response.json()

# @pytest.mark.order3
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