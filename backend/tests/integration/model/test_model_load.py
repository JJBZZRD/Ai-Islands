import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.api.main import app
from backend.core.exceptions import ModelError

@pytest.fixture
def client():
    return TestClient(app)

def test_load_model_success(client, model_info):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    
    with patch("backend.controlers.model_control.ModelControl.load_model") as mock_load:
        mock_load.return_value = True
        response = client.post(f"/model/load?model_id={model_id}")
    
    assert response.status_code == 200
    assert response.json() == {"message": f"Model {model_id} loaded successfully", "data": {}}
    mock_load.assert_called_once_with(model_id)

def test_load_model_not_found(client):
    model_id = "NonExistentModel"
    
    with patch("backend.controlers.model_control.ModelControl.load_model", side_effect=ValueError("Model not found")):
        response = client.post(f"/model/load?model_id={model_id}")
    
    assert response.status_code == 404
    assert "Model not found" in response.json()["error"]["message"]

def test_load_model_error(client):
    model_id = "ErrorModel"
    
    with patch("backend.controlers.model_control.ModelControl.load_model", side_effect=ModelError("Failed to load model")):
        response = client.post(f"/model/load?model_id={model_id}")
    
    assert response.status_code == 500
    assert "Failed to load model" in response.json()["error"]["message"]

def test_load_model_file_not_found(client):
    model_id = "MissingFileModel"
    
    with patch("backend.controlers.model_control.ModelControl.load_model", side_effect=FileNotFoundError("Model file not found")):
        response = client.post(f"/model/load?model_id={model_id}")
    
    assert response.status_code == 500
    assert "Model file not found" in response.json()["error"]["message"]