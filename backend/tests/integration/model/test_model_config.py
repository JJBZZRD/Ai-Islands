import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.routes.model_routes import ModelRouter
from backend.controlers.model_control import ModelControl
from fastapi import FastAPI

@pytest.fixture
def app(model_control):
    app = FastAPI()
    model_router = ModelRouter(model_control)
    app.include_router(model_router.router, prefix="/model")
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def model_control():
    return ModelControl()

@pytest.fixture(autouse=True)
def mock_settings_service():
    with patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'):
        yield

def test_configure_model_success(client, mock_library_entry, model_info_library):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    config_data = {"param1": "value1", "param2": "value2"}
    
    with patch('backend.controlers.model_control.LibraryControl.update_model_config', return_value=True), \
         patch('backend.controlers.model_control.ModelControl.is_model_loaded', return_value=False):
        
        response = client.post("/model/configure", json={
            "model_id": model_id,
            "data": config_data
        })
    
    assert response.status_code == 200
    assert response.json() == {"message": {"message": f"Model {model_id} configuration updated in library"}, "data": {}}

def test_configure_model_not_found(client):
    model_id = "non_existent_model"
    config_data = {"param1": "value1"}
    
    with patch('backend.controlers.model_control.LibraryControl.update_model_config', side_effect=KeyError(f"Model {model_id} not found in library")):
        response = client.post("/model/configure", json={
            "model_id": model_id,
            "data": config_data
        })
    
    print(f"test_configure_model_not_found - Status Code: {response.status_code}")
    print(f"test_configure_model_not_found - Response JSON: {response.json()}")
    
    assert response.status_code == 200
    assert "not found in library" in str(response.json())

def test_configure_model_update_failed(client, mock_library_entry):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    config_data = {"param1": "value1"}
    
    with patch('backend.controlers.model_control.LibraryControl.update_model_config', return_value=False):
        response = client.post("/model/configure", json={
            "model_id": model_id,
            "data": config_data
        })
    
    assert response.status_code == 200
    response_json = response.json()
    print(f"Update failed response: {response_json}")
    assert "Failed to update configuration" in str(response_json)

def test_configure_model_reload(client, mock_library_entry, model_info_library):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    config_data = {"param1": "value1"}
    
    with patch('backend.controlers.model_control.LibraryControl.update_model_config', return_value=True), \
         patch('backend.controlers.model_control.ModelControl.is_model_loaded', return_value=True), \
         patch('backend.controlers.model_control.ModelControl.unload_model') as mock_unload, \
         patch('backend.controlers.model_control.ModelControl.load_model') as mock_load:
        
        response = client.post("/model/configure", json={
            "model_id": model_id,
            "data": config_data
        })
    
    assert response.status_code == 200
    assert response.json() == {"message": {"message": f"Model {model_id} configuration updated in library"}, "data": {}}
    mock_unload.assert_called_once_with(model_id)
    mock_load.assert_called_once_with(model_id)
