import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
import json

from backend.api.main import app
from backend.controlers.library_control import LibraryControl
from backend.core.config import DOWNLOADED_MODELS_PATH
from backend.core.exceptions import FileReadError

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_library_control():
    return LibraryControl()

def test_get_model_info_library(client):
    mock_library_data = {
        "model1": {
            "base_model": "base_model1",
            "config": {"param1": "value1"},
            "is_customised": False
        },
        "model2": {
            "base_model": "base_model2",
            "config": {"param2": "value2"},
            "is_customised": True
        }
    }
    
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_library_data))):
        with patch("backend.controlers.library_control.DOWNLOADED_MODELS_PATH", DOWNLOADED_MODELS_PATH):
            response = client.get("/library/get-model-info-library?model_id=model1")
    
    assert response.status_code == 200
    assert response.json() == mock_library_data["model1"]

def test_get_model_info_library_not_found(client):
    with patch("backend.controlers.library_control.LibraryControl.get_model_info_library", return_value=None):
        response = client.get("/library/get-model-info-library?model_id=non_existent_model")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Model non_existent_model not found in library"

def test_get_model_info_library_file_read_error(client):
    with patch("backend.controlers.library_control.LibraryControl.get_model_info_library", side_effect=FileReadError("Error reading file")):
        response = client.get("/library/get-model-info-library?model_id=model1")
    
    assert response.status_code == 500
    assert "Error reading file" in response.json()["detail"]