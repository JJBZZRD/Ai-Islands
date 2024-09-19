import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.api.main import app
from backend.core.exceptions import ModelNotAvailableError, ModelError

@pytest.fixture
def client():
    return TestClient(app)

def test_download_model_success(client, model_info):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    
    with patch("backend.controlers.model_control.ModelControl.download_model") as mock_download:
        response = client.post(f"/model/download-model?model_id={model_id}")
    
    # Note: We don't check for library updates or file creation here
    # because these are handled internally by ModelControl.download_model
    # and are covered by unit tests in test_model_control_download.py
    assert response.status_code == 200
    assert response.json()["data"] == {}
    assert response.json()["message"] == f"Model {model_id} downloaded successfully"
    mock_download.assert_called_once_with(model_id, None)

def test_download_model_not_available(client):
    model_id = "NonExistentModel"
    
    with patch("backend.controlers.model_control.ModelControl.download_model", side_effect=ModelNotAvailableError("Model not available")):
        response = client.post(f"/model/download-model?model_id={model_id}")

    assert response.status_code == 503
    assert "Model not available" in response.json()["error"]["message"]

def test_download_model_error(client):
    model_id = "ErrorModel"
    
    with patch("backend.controlers.model_control.ModelControl.download_model", side_effect=ModelError("Download failed")):
        response = client.post(f"/model/download-model?model_id={model_id}")

    assert response.status_code == 500
    assert "Download failed" in response.json()["error"]["message"]

def test_download_model_with_auth(client, model_info):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    auth_token = "test_token"
    
    with patch("backend.controlers.model_control.ModelControl.download_model") as mock_download:
        response = client.post(f"/model/download-model?model_id={model_id}&auth_token={auth_token}")
 
    assert response.status_code == 200
    assert response.json()["data"] == {}
    assert response.json()["message"] == f"Model {model_id} downloaded successfully"
    mock_download.assert_called_once_with(model_id, auth_token)