import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

@pytest.mark.order1
def test_get_full_model_index():
    response = client.get("/library/get-full-model-index")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

@pytest.mark.order2
def test_get_full_library():
    response = client.get("/library/get-full-library")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

@pytest.mark.order3
def test_get_model_info_library():
    response = client.get("/library/get-model-info-library", params={"model_id": "ibm/granite-20b-multilingual"})
    response_json = response.json()
    print("Get Model Info Library Response JSON:", response_json)  # Debug print
    assert response.status_code == 200
    assert "base_model" in response_json  # Check if 'base_model' is in the response JSON
    assert response_json["base_model"] == "ibm/granite-20b-multilingual"  # Validate the value of 'base_model'

@pytest.mark.order5
def test_update_model_config():
    update_request = {
        "model_id": "ibm/granite-20b-multilingual",
        "new_config": {"parameters": {"temperature": "0.1"}}
    }
    response = client.post("/library/update-model-config", json=update_request)
    print("Update Model Config Response JSON:", response.json())  # Debug print
    assert response.status_code == 200
    assert response.json()["message"] == "Configuration updated for model ibm/granite-20b-multilingual"

@pytest.mark.order6
def test_save_new_model():
    save_request = {
        "model_id": "ibm/granite-20b-multilingual",
        "new_model_id": "ibm/granite-20b-multilingual",
        "new_config": {"parameters": {"temperature": "0.1"}}  # Added new_config field
    }
    response = client.post("/library/save-new-model", json=save_request)
    print("Save New Model Response JSON:", response.json())  # Debug print
    assert response.status_code == 200
    assert response.json() == {"message": "New model ibm/granite-20b-multilingual saved successfully"}  # Updated expected message

@pytest.mark.order7
def test_update_model_id():
    update_request = {
        "model_id": "ibm/granite-20b-multilingual",  # Corrected model_id
        "new_model_id": "updated_ibm/granite-20b-multilingual",
        "new_config": {}
    }
    response = client.post("/library/update-model-id", json=update_request)
    print("Update Model ID Response JSON:", response.json())  # Debug print
    assert response.status_code == 200
    assert response.json() == {"message": "Model ID updated from ibm/granite-20b-multilingual to updated_ibm/granite-20b-multilingual"}  # Updated expected message

@pytest.mark.order8
def test_restore_model_id():
    update_request = {
        "model_id": "updated_ibm/granite-20b-multilingual",  # Corrected model_id
        "new_model_id": "ibm/granite-20b-multilingual",
        "new_config": {}
    }
    response = client.post("/library/update-model-id", json=update_request)
    print("Update Model ID Response JSON:", response.json())  # Debug print
    assert response.status_code == 200
    assert response.json() == {"message": "Model ID updated from updated_ibm/granite-20b-multilingual to ibm/granite-20b-multilingual"}

# @pytest.mark.order8
# def test_delete_model():
#     response = client.delete("/library/delete-model", params={"model_id": "updated_ibm/granite-20b-multilingual"})
#     print("Delete Model Response JSON:", response.json())  # Debug print
#     assert response.status_code == 200
#     assert response.json() == {"message": "Model updated_model_id deleted from library"}