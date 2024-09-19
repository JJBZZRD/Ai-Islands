import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
import json

from backend.api.main import app
from backend.controlers.library_control import LibraryControl
from backend.core.config import MODEL_INDEX_PATH
from backend.core.exceptions import FileReadError

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_library_control():
    return LibraryControl()

def test_get_model_info_index(client):
    mock_index_data = {
        "model1": {
            "config": {"param1": "value1"},
            "other_info": "info1"
        },
        "model2": {
            "config": {"param2": "value2"},
            "other_info": "info2"
        }
    }
    
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_index_data))):
        with patch("backend.controlers.library_control.MODEL_INDEX_PATH", MODEL_INDEX_PATH):
            response = client.get("/library/get-model-info-index?model_id=model1")
    
    assert response.status_code == 200
    assert response.json() == mock_index_data["model1"]

def test_get_model_info_index_not_found(client):
    with patch("backend.controlers.library_control.LibraryControl.get_model_info_index", return_value=None):
        response = client.get("/library/get-model-info-index?model_id=non_existent_model")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Model non_existent_model not found in index"

def test_get_model_info_index_file_read_error(client):
    with patch("backend.controlers.library_control.LibraryControl.get_model_info_index", side_effect=FileReadError("Error reading file")):
        response = client.get("/library/get-model-info-index?model_id=model1")
    
    assert response.status_code == 500
    assert "Error reading file" in response.json()["detail"]