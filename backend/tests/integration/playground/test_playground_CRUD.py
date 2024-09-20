import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.routes.playground_routes import PlaygroundRouter
from backend.controlers.playground_control import PlaygroundControl
from backend.controlers.model_control import ModelControl
from backend.data_utils.json_handler import JSONHandler
import asyncio

@pytest.fixture
def mock_playground_control(mock_playground_data):
    with patch('backend.data_utils.json_handler.JSONHandler.read_json', return_value=mock_playground_data), \
         patch('backend.data_utils.json_handler.JSONHandler.write_json', return_value=True):
        yield PlaygroundControl(ModelControl())

@pytest.fixture
def app(mock_playground_control):
    app = FastAPI()
    playground_router = PlaygroundRouter(mock_playground_control)
    app.include_router(playground_router.router, prefix="/playground")
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_settings_service():
    with patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'):
        yield

def test_create_playground(client, mock_playground_data):
    response = client.post("/playground/create", json={"description": "New playground"})
    assert response.status_code == 201
    assert "playground_id" in response.json()["data"]
    assert "playground" in response.json()["data"]
    assert response.json()["data"]["playground"]["description"] == "New playground"

def test_create_playground_already_exists(client, mock_playground_data):
    response = client.post("/playground/create", json={"playground_id": "test_playground", "description": "Duplicate playground"})
    assert response.status_code == 409
    assert "error" in response.json()
    assert "already exists" in response.json()["error"]["message"].lower()

def test_update_playground(client, mock_playground_data):
    update_data = {
        "playground_id": "test_playground",
        "new_playground_id": "updated_playground",
        "description": "Updated description"
    }
    response = client.put("/playground/update", json=update_data)
    assert response.status_code == 200
    assert response.json()["data"]["playground_id"] == "updated_playground"
    assert response.json()["data"]["playground"]["description"] == "Updated description"

def test_update_playground_not_found(client, mock_playground_data):
    update_data = {
        "playground_id": "non_existent_playground",
        "description": "Updated description"
    }
    response = client.put("/playground/update", json=update_data)
    assert response.status_code == 404
    assert "error" in response.json()
    assert "does not exist" in response.json()["error"]["message"].lower()

def test_delete_playground(client, mock_playground_data):
    response = client.delete("/playground/delete?playground_id=test_playground")
    assert response.status_code == 204

def test_delete_playground_not_found(client, mock_playground_data):
    response = client.delete("/playground/delete?playground_id=non_existent_playground")
    assert response.status_code == 404
    assert "error" in response.json()
    assert "does not exist" in response.json()["error"]["message"].lower()

def test_add_model_to_playground(client, mock_playground_data):
    with patch('backend.controlers.library_control.LibraryControl.get_model_info_library', return_value={"input": "text", "output": "text"}):
        response = client.post("/playground/add-model", json={
            "playground_id": "test_playground",
            "model_id": "new_model"
        })
    assert response.status_code == 200
    assert "new_model" in response.json()["data"]["models"]

def test_add_model_to_playground_not_found(client, mock_playground_data):
    response = client.post("/playground/add-model", json={
        "playground_id": "non_existent_playground",
        "model_id": "model1"
    })
    assert response.status_code == 404
    assert "error" in response.json()
    assert "not found" in response.json()["error"]["message"].lower()

def test_remove_model_from_playground(client, mock_playground_data):
    response = client.post("/playground/remove-model", json={
        "playground_id": "test_playground",
        "model_id": "model1"
    })
    assert response.status_code == 204

def test_remove_model_from_playground_not_found(client, mock_playground_data):
    response = client.post("/playground/remove-model", json={
        "playground_id": "test_playground",
        "model_id": "non_existent_model"
    })
    assert response.status_code == 204