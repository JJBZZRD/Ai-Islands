import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open
import json

from backend.api.main import app
from backend.controlers.library_control import LibraryControl

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_library_control():
    return LibraryControl()

def test_get_full_library(client):
    mock_library_data = {
        "model1": {"description": "Test model 1", "config": {"param1": "value1"}},
        "model2": {"description": "Test model 2", "config": {"param2": "value2"}}
    }
    
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_library_data))):
        response = client.get("/library/get-full-library")
    
    assert response.status_code == 200
    assert response.json() == mock_library_data